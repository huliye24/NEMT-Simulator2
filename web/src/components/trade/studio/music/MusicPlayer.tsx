"use client";

import Image from "next/image";
import { useEffect, useRef, useState } from "react";
import musicMuse from "../assets/emergentix-music-muse-v2.png";
import styles from "./MusicPlayer.module.css";

interface MusicTrack { id: string; title: string; artist: string; file: string; }
interface MusicPlayerProps { compact?: boolean; split?: boolean; }

const LOCAL_MUSIC_ORIGIN = "http://127.0.0.1:8765";
const TRACKS: MusicTrack[] = [
  { id: "rain", title: "大雨还在下", artist: "1个球", file: "1个球-大雨还在下.flac" },
  { id: "3611", title: "3611", artist: "陈子晴", file: "3611 - 陈子晴.flac" },
  { id: "9420", title: "9420", artist: "麦小兜", file: "9420 - 麦小兜.flac" },
  { id: "second", title: "秒针", artist: "阿梨粤", file: "阿梨粤-秒针.flac" },
  { id: "dream", title: "追梦人", artist: "阿木", file: "阿木-追梦人.flac" },
  { id: "answer", title: "你的答案", artist: "阿冗", file: "阿冗-你的答案.flac" },
  { id: "105", title: "热爱105°C的你", artist: "阿肆", file: "阿肆-热爱105°C的你.flac" },
  { id: "tide", title: "潮汐 (Natural)", artist: "安苏羽 / 傅梦彤", file: "安苏羽&傅梦彤-潮汐(Natural).flac" },
];

function trackUrl(track: MusicTrack): string { return `${LOCAL_MUSIC_ORIGIN}/${encodeURIComponent(track.file)}`; }
function formatTime(value: number): string {
  if (!Number.isFinite(value)) return "0:00";
  return `${Math.floor(value / 60)}:${Math.floor(value % 60).toString().padStart(2, "0")}`;
}

export default function MusicPlayer({ compact = false, split = false }: MusicPlayerProps) {
  const [trackIndex, setTrackIndex] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [volume, setVolume] = useState(50);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const resumeAfterTrackChangeRef = useRef(false);
  const track = TRACKS[trackIndex];

  useEffect(() => { if (audioRef.current) audioRef.current.volume = volume / 100; }, [volume]);
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;
    setCurrentTime(0); setDuration(0); audio.load();
    if (!resumeAfterTrackChangeRef.current) return;
    resumeAfterTrackChangeRef.current = false;
    audio.play().then(() => { setPlaying(true); setError(null); }).catch(() => {
      setPlaying(false); setError("无法播放本地 FLAC，请确认 E:\\FLAC 音乐服务仍在运行。");
    });
  }, [trackIndex]);

  async function togglePlayback(): Promise<void> {
    const audio = audioRef.current;
    if (!audio) return;
    try {
      if (playing) { audio.pause(); setPlaying(false); }
      else { await audio.play(); setPlaying(true); setError(null); }
    } catch { setPlaying(false); setError("无法播放本地 FLAC，请确认 E:\\FLAC 音乐服务仍在运行。"); }
  }
  function chooseTrack(index: number, resume = playing): void {
    audioRef.current?.pause(); resumeAfterTrackChangeRef.current = resume; setPlaying(false); setTrackIndex(index);
  }
  function stepTrack(direction: number): void { chooseTrack((trackIndex + direction + TRACKS.length) % TRACKS.length); }
  function seekTo(value: number): void { if (audioRef.current) audioRef.current.currentTime = value; setCurrentTime(value); }

  const audio = <audio ref={audioRef} src={trackUrl(track)} preload="metadata" onEnded={() => stepTrack(1)} onLoadedMetadata={(event) => setDuration(event.currentTarget.duration)} onTimeUpdate={(event) => setCurrentTime(event.currentTarget.currentTime)} onError={() => { setPlaying(false); setError("曲目读取失败，请确认本地音乐服务可访问。"); }} />;

  if (compact) {
    return (
      <section className={`${styles.ipPlayer} ${split ? styles.split : ""}`} aria-label="音乐播放器">
        {audio}
        <div className={styles.ipVisual} aria-label="Emergentix 音乐人物 IP">
          <span className={styles.ipLabel}>EMERGENTIX<br />RADIO</span>
          <span className={styles.ipNumber}>IP / 01</span>
          <Image src={musicMuse} alt="佩戴耳机、身穿米色风衣的 Emergentix 音乐人物 IP" priority sizes="420px" className={styles.ipMuse} />
        </div>
        <div className={styles.miniPlayer}>
          <button type="button" className={styles.miniPlay} onClick={() => void togglePlayback()} aria-label={playing ? "暂停" : "播放"}>{playing ? "Ⅱ" : "▶"}</button>
          <div className={styles.miniTrack}>
            <strong>{track.title}</strong><span>{track.artist}</span>
            <input className={styles.miniProgress} type="range" min="0" max={duration || 0} step="0.1" value={currentTime} onChange={(event) => seekTo(Number(event.target.value))} aria-label="播放进度" />
          </div>
          <span className={styles.miniTime}>{formatTime(currentTime)}</span>
          <button type="button" className={styles.miniSkip} onClick={() => stepTrack(-1)} aria-label="上一首">←</button>
          <button type="button" className={styles.miniSkip} onClick={() => stepTrack(1)} aria-label="下一首">→</button>
        </div>
        {!split ? <div className={styles.miniPlaylist} aria-label="选择歌曲">
          {TRACKS.map((item, index) => <button type="button" key={item.id} className={index === trackIndex ? styles.miniActive : ""} onClick={() => chooseTrack(index)} aria-label={`播放 ${item.title}`}>{(index + 1).toString().padStart(2, "0")}</button>)}
        </div> : null}
        {error ? <p className={styles.miniError} role="alert">{error}</p> : null}
      </section>
    );
  }

  return (
    <section className={`${styles.player} ${compact ? styles.compact : ""}`} aria-label="音乐播放器">
      {audio}
      <div className={styles.content}>
        <div className={styles.copy}>
          <p className={styles.eyebrow}><span>EMERGENTIX RADIO</span><span>LOCAL / 01</span></p>
          <p className={styles.title}>{track.title}</p>
          <p className={styles.subtitle}>{track.artist}<span aria-hidden="true">↗</span></p>
        </div>
        <div className={styles.transport}>
          <button type="button" className={styles.play} onClick={() => void togglePlayback()} aria-label={playing ? "暂停" : "播放"}>{playing ? "Ⅱ" : "▶"}</button>
          <div className={styles.timeline}>
            <input className={styles.progress} type="range" min="0" max={duration || 0} step="0.1" value={currentTime} onChange={(event) => seekTo(Number(event.target.value))} aria-label="播放进度" />
            <div className={styles.time}><span>{formatTime(currentTime)}</span><span>{formatTime(duration)}</span></div>
          </div>
          <div className={styles.skipControls}>
            <button type="button" className={styles.skip} onClick={() => stepTrack(-1)} aria-label="上一首">←</button>
            <button type="button" className={styles.skip} onClick={() => stepTrack(1)} aria-label="下一首">→</button>
          </div>
        </div>
        <div className={styles.volumeWrap}><span>VOL</span><input className={styles.volume} type="range" min="0" max="100" value={volume} onChange={(event) => setVolume(Number(event.target.value))} aria-label="音量" /><span>{volume.toString().padStart(2, "0")}</span></div>
      </div>
      <div className={styles.visual} aria-hidden="true">
        <span className={styles.scribble}>FLOW<br />STATE</span>
        <Image src={musicMuse} alt="" priority sizes={compact ? "420px" : "(max-width: 700px) 100vw, 52vw"} className={styles.muse} />
      </div>
      <nav className={styles.trackRail} aria-label="选择歌曲">
        {TRACKS.map((item, index) => <button type="button" key={item.id} className={`${styles.trackButton} ${index === trackIndex ? styles.activeTrack : ""}`} onClick={() => chooseTrack(index)}><span>{(index + 1).toString().padStart(2, "0")}</span><strong>{item.title}</strong><small>{item.artist}</small></button>)}
      </nav>
      {error ? <p className={styles.error} role="alert">{error}</p> : null}
    </section>
  );
}
