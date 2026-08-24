/**
 * Copyright 2026 NEMT Lab
 *
 * IndexedDB 持久化存储适配器
 */

// ============================================
// 类型定义
// ============================================

export interface StorageOptions {
  /** 数据库名称 */
  dbName: string;
  /** 版本号 */
  version: number;
  /** 对象存储列表 */
  stores: StoreConfig[];
}

export interface StoreConfig {
  /** 存储名称 */
  name: string;
  /** 主键配置 */
  keyPath: string;
  /** 是否自动递增 */
  autoIncrement?: boolean;
  /** 索引配置 */
  indexes?: IndexConfig[];
  /** 是否启用版本迁移 */
  migrations?: Migration[];
}

export interface IndexConfig {
  /** 索引名称 */
  name: string;
  /** 索引字段路径 */
  keyPath: string | string[];
  /** 是否唯一 */
  unique?: boolean;
  /** 是否多值 */
  multiEntry?: boolean;
}

export interface Migration {
  /** 目标版本 */
  version: number;
  /** 迁移函数 */
  up: (db: IDBDatabase) => void;
  /** 回滚函数 */
  down?: (db: IDBDatabase) => void;
}

// ============================================
// 存储错误
// ============================================

export class StorageError extends Error {
  constructor(
    message: string,
    public code: 'NOT_FOUND' | 'TRANSACTION_FAILED' | 'VERSION_ERROR' | 'UNKNOWN',
    public originalError?: Error
  ) {
    super(message);
    this.name = 'StorageError';
  }
}

// ============================================
// IndexedDB 包装器
// ============================================

export class Storage {
  private db: IDBDatabase | null = null;
  private dbName: string;
  private version: number;
  private stores: Map<string, StoreConfig> = new Map();
  private initPromise: Promise<void> | null = null;

  constructor(options: StorageOptions) {
    this.dbName = options.dbName;
    this.version = options.version;
    options.stores.forEach(store => this.stores.set(store.name, store));
  }

  /**
   * 初始化数据库
   */
  async init(): Promise<void> {
    if (this.db) return;
    if (this.initPromise) return this.initPromise;

    this.initPromise = new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, this.version);

      request.onerror = () => {
        reject(new StorageError(
          `Failed to open database: ${this.dbName}`,
          'UNKNOWN',
          request.error as Error
        ));
      };

      request.onsuccess = () => {
        this.db = request.result;
        console.log(`[Storage] Database ${this.dbName} opened successfully`);
        resolve();
      };

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;
        console.log(`[Storage] Upgrading database from version ${event.oldVersion} to ${event.newVersion}`);

        // 执行迁移
        this.stores.forEach((config, name) => {
          if (!db.objectStoreNames.contains(name)) {
            this.createStore(db, config);
          }
        });
      };
    });

    return this.initPromise;
  }

  /**
   * 创建对象存储
   */
  private createStore(db: IDBDatabase, config: StoreConfig): IDBObjectStore {
    const store = db.createObjectStore(config.name, {
      keyPath: config.keyPath,
      autoIncrement: config.autoIncrement ?? false
    });

    // 创建索引
    config.indexes?.forEach(index => {
      store.createIndex(index.name, index.keyPath, {
        unique: index.unique ?? false,
        multiEntry: index.multiEntry ?? false
      });
    });

    console.log(`[Storage] Created store: ${config.name}`);
    return store;
  }

  /**
   * 获取事务
   */
  private getTransaction(
    storeName: string,
    mode: IDBTransactionMode = 'readonly'
  ): IDBTransaction {
    if (!this.db) {
      throw new StorageError('Database not initialized', 'UNKNOWN');
    }
    return this.db.transaction(storeName, mode);
  }

  /**
   * 获取对象存储
   */
  private getStore(
    storeName: string,
    mode: IDBTransactionMode = 'readonly'
  ): IDBObjectStore {
    const transaction = this.getTransaction(storeName, mode);
    const store = transaction.objectStore(storeName);

    transaction.onerror = () => {
      throw new StorageError(
        `Transaction failed for store: ${storeName}`,
        'TRANSACTION_FAILED'
      );
    };

    return store;
  }

  /**
   * 插入数据
   */
  async put<T>(storeName: string, data: T): Promise<T> {
    return new Promise((resolve, reject) => {
      try {
        const store = this.getStore(storeName, 'readwrite');
        const request = store.put(data);

        request.onsuccess = () => resolve(data);
        request.onerror = () => reject(new StorageError(
          `Failed to put data in ${storeName}`,
          'TRANSACTION_FAILED',
          request.error as Error
        ));
      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * 插入数据 (唯一)
   */
  async add<T>(storeName: string, data: T): Promise<T> {
    return new Promise((resolve, reject) => {
      try {
        const store = this.getStore(storeName, 'readwrite');
        const request = store.add(data);

        request.onsuccess = () => resolve(data);
        request.onerror = () => reject(new StorageError(
          `Failed to add data in ${storeName} (key may already exist)`,
          'TRANSACTION_FAILED',
          request.error as Error
        ));
      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * 获取数据
   */
  async get<T>(storeName: string, key: IDBValidKey): Promise<T | undefined> {
    return new Promise((resolve, reject) => {
      try {
        const store = this.getStore(storeName, 'readonly');
        const request = store.get(key);

        request.onsuccess = () => resolve(request.result as T);
        request.onerror = () => reject(new StorageError(
          `Failed to get data from ${storeName}`,
          'TRANSACTION_FAILED',
          request.error as Error
        ));
      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * 获取所有数据
   */
  async getAll<T>(storeName: string): Promise<T[]> {
    return new Promise((resolve, reject) => {
      try {
        const store = this.getStore(storeName, 'readonly');
        const request = store.getAll();

        request.onsuccess = () => resolve(request.result as T[]);
        request.onerror = () => reject(new StorageError(
          `Failed to get all data from ${storeName}`,
          'TRANSACTION_FAILED',
          request.error as Error
        ));
      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * 删除数据
   */
  async delete(storeName: string, key: IDBValidKey): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        const store = this.getStore(storeName, 'readwrite');
        const request = store.delete(key);

        request.onsuccess = () => resolve();
        request.onerror = () => reject(new StorageError(
          `Failed to delete data from ${storeName}`,
          'TRANSACTION_FAILED',
          request.error as Error
        ));
      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * 清空存储
   */
  async clear(storeName: string): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        const store = this.getStore(storeName, 'readwrite');
        const request = store.clear();

        request.onsuccess = () => resolve();
        request.onerror = () => reject(new StorageError(
          `Failed to clear ${storeName}`,
          'TRANSACTION_FAILED',
          request.error as Error
        ));
      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * 按索引查询
   */
  async getByIndex<T>(
    storeName: string,
    indexName: string,
    query: IDBValidKey | IDBKeyRange
  ): Promise<T[]> {
    return new Promise((resolve, reject) => {
      try {
        const store = this.getStore(storeName, 'readonly');
        const index = store.index(indexName);
        const request = index.getAll(query);

        request.onsuccess = () => resolve(request.result as T[]);
        request.onerror = () => reject(new StorageError(
          `Failed to query by index ${indexName} in ${storeName}`,
          'TRANSACTION_FAILED',
          request.error as Error
        ));
      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * 批量操作
   */
  async bulkPut<T>(storeName: string, items: T[]): Promise<T[]> {
    return new Promise((resolve, reject) => {
      try {
        const store = this.getStore(storeName, 'readwrite');
        const results: T[] = [];

        let completed = 0;
        let hasError = false;

        items.forEach(item => {
          const request = store.put(item);

          request.onsuccess = () => {
            results.push(item);
            completed++;
            if (completed === items.length && !hasError) {
              resolve(results);
            }
          };

          request.onerror = () => {
            if (!hasError) {
              hasError = true;
              reject(new StorageError(
                `Failed to bulk put in ${storeName}`,
                'TRANSACTION_FAILED',
                request.error as Error
              ));
            }
          };
        });
      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * 计数
   */
  async count(storeName: string): Promise<number> {
    return new Promise((resolve, reject) => {
      try {
        const store = this.getStore(storeName, 'readonly');
        const request = store.count();

        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(new StorageError(
          `Failed to count in ${storeName}`,
          'TRANSACTION_FAILED',
          request.error as Error
        ));
      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * 关闭数据库
   */
  close(): void {
    if (this.db) {
      this.db.close();
      this.db = null;
      console.log(`[Storage] Database ${this.dbName} closed`);
    }
  }

  /**
   * 删除数据库
   */
  static async deleteDatabase(dbName: string): Promise<void> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.deleteDatabase(dbName);

      request.onsuccess = () => {
        console.log(`[Storage] Database ${dbName} deleted`);
        resolve();
      };

      request.onerror = () => reject(new StorageError(
        `Failed to delete database: ${dbName}`,
        'UNKNOWN',
        request.error as Error
      ));
    });
  }
}

// ============================================
// NEMT Platform 存储配置
// ============================================

export const nemtStorage = new Storage({
  dbName: 'nemt-platform',
  version: 1,
  stores: [
    {
      name: 'strategies',
      keyPath: 'id',
      indexes: [
        { name: 'status', keyPath: 'status' },
        { name: 'author', keyPath: 'author' },
        { name: 'createdAt', keyPath: 'createdAt' },
        { name: 'updatedAt', keyPath: 'updatedAt' }
      ]
    },
    {
      name: 'capsules',
      keyPath: 'id',
      indexes: [
        { name: 'type', keyPath: 'type' },
        { name: 'status', keyPath: 'status' }
      ]
    },
    {
      name: 'settings',
      keyPath: 'key',
      indexes: [
        { name: 'category', keyPath: 'category' }
      ]
    },
    {
      name: 'errorLogs',
      keyPath: 'id',
      indexes: [
        { name: 'severity', keyPath: 'severity' },
        { name: 'timestamp', keyPath: 'timestamp' }
      ]
    },
    {
      name: 'undoHistory',
      keyPath: 'id',
      indexes: [
        { name: 'timestamp', keyPath: 'timestamp' }
      ]
    }
  ]
});

// ============================================
// 自动保存 Hook
// ============================================

export async function autoSave<T>(
  key: string,
  data: T,
  storage: Storage = nemtStorage
): Promise<void> {
  await storage.put(`autosave_${key}`, {
    key,
    data,
    timestamp: Date.now()
  });
}

export async function autoLoad<T>(
  key: string,
  storage: Storage = nemtStorage
): Promise<T | null> {
  try {
    const result = await storage.get<{ key: string; data: T; timestamp: number }>(
      'autosave',
      key
    );
    return result?.data ?? null;
  } catch {
    return null;
  }
}
