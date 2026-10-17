// NEMT Web Alpha 006 — IndexedDB implementation
// ---------------------------------------------------------------
// Used for large or list-shaped data: analysis history, journal
// entries authored locally. Each KeyValueStore key maps to one
// "row" in the object store, so reads/writes stay O(1).
//
// The DB is opened lazily on first use; on older browsers we
// fall back to LocalStore so the rest of the app keeps working.
// ---------------------------------------------------------------

import type { KeyValueStore } from "./storage";
import { LocalStore } from "./localStore";

const DB_NAME = "nemt-memory";
const DB_VERSION = 1;
const STORE = "kv";

function isAvailable(): boolean {
  return typeof window !== "undefined" && "indexedDB" in window;
}

function openDb(): Promise<IDBDatabase | null> {
  if (!isAvailable()) return Promise.resolve(null);
  return new Promise((resolve) => {
    let req: IDBOpenDBRequest;
    try {
      req = window.indexedDB.open(DB_NAME, DB_VERSION);
    } catch {
      resolve(null);
      return;
    }
    req.onupgradeneeded = () => {
      const db = req.result;
      if (!db.objectStoreNames.contains(STORE)) {
        db.createObjectStore(STORE);
      }
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => {
      console.warn("[memory] IndexedDB open failed; falling back to localStorage");
      resolve(null);
    };
    req.onblocked = () => {
      console.warn("[memory] IndexedDB blocked by another connection");
      resolve(null);
    };
  });
}

export class IdbStore implements KeyValueStore {
  private dbPromise: Promise<IDBDatabase | null> | null = null;

  private async db(): Promise<IDBDatabase | null> {
    if (!this.dbPromise) this.dbPromise = openDb();
    return this.dbPromise;
  }

  async get<T>(key: string): Promise<T | null> {
    const db = await this.db();
    if (!db) return LocalStore.get<T>(key);
    return new Promise((resolve) => {
      const tx = db.transaction(STORE, "readonly");
      const req = tx.objectStore(STORE).get(key);
      req.onsuccess = () => resolve((req.result as T | undefined) ?? null);
      req.onerror = () => {
        console.warn(`[memory] IdbStore.get(${key}) failed:`, req.error);
        resolve(null);
      };
    });
  }

  async set<T>(key: string, value: T): Promise<void> {
    const db = await this.db();
    if (!db) return LocalStore.set<T>(key, value);
    return new Promise((resolve) => {
      const tx = db.transaction(STORE, "readwrite");
      tx.objectStore(STORE).put(value, key);
      tx.oncomplete = () => resolve();
      tx.onerror = () => {
        console.warn(`[memory] IdbStore.set(${key}) failed:`, tx.error);
        resolve();
      };
    });
  }

  async remove(key: string): Promise<void> {
    const db = await this.db();
    if (!db) return LocalStore.remove(key);
    return new Promise((resolve) => {
      const tx = db.transaction(STORE, "readwrite");
      tx.objectStore(STORE).delete(key);
      tx.oncomplete = () => resolve();
      tx.onerror = () => {
        console.warn(`[memory] IdbStore.remove(${key}) failed:`, tx.error);
        resolve();
      };
    });
  }

  async keys(prefix?: string): Promise<string[]> {
    const db = await this.db();
    if (!db) return LocalStore.keys(prefix);
    return new Promise((resolve) => {
      const tx = db.transaction(STORE, "readonly");
      const req = tx.objectStore(STORE).getAllKeys();
      req.onsuccess = () => {
        const all = (req.result as IDBValidKey[]).map((k) => String(k));
        resolve(prefix ? all.filter((k) => k.startsWith(prefix)) : all);
      };
      req.onerror = () => resolve([]);
    });
  }

  async clear(): Promise<void> {
    const db = await this.db();
    if (!db) return LocalStore.clear();
    return new Promise((resolve) => {
      const tx = db.transaction(STORE, "readwrite");
      tx.objectStore(STORE).clear();
      tx.oncomplete = () => resolve();
      tx.onerror = () => resolve();
    });
  }
}
