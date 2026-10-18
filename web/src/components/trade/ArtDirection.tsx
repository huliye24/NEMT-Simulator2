"use client";

/** Visual system for the mobile trading surface.
 * Kept beside the components so the direction lock stays intact.
 */
export default function ArtDirection() {
  return (
    <>
      <div className="nemt-art-layer" aria-hidden="true">
        <span className="nemt-brush nemt-brush-a" />
        <span className="nemt-brush nemt-brush-b" />
        <span className="nemt-ink nemt-ink-a" />
        <span className="nemt-ink nemt-ink-b" />
      </div>
      <style jsx global>{`
        :root {
          --art-paper: #f0eadf;
          --art-ink: #161714;
          --art-green: #123f39;
          --art-red: #c84538;
          --art-gold: #c59643;
        }
        body { background: var(--art-paper) !important; }
        .trade-shell {
          position: relative;
          isolation: isolate;
          color: var(--art-ink) !important;
          background:
            radial-gradient(circle at 12% 18%, rgba(197,150,67,.12), transparent 24rem),
            linear-gradient(115deg, rgba(255,255,255,.72), rgba(239,232,218,.94)) !important;
          font-family: Inter, "PingFang SC", "Microsoft YaHei", sans-serif;
        }
        .trade-shell::after {
          content: ""; position: fixed; inset: 0; z-index: -3; pointer-events: none;
          opacity: .16; mix-blend-mode: multiply;
          background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='160'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.88' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='.24'/%3E%3C/svg%3E");
        }
        .nemt-art-layer { position: fixed; inset: 0; z-index: 0; overflow: hidden; pointer-events: none; mix-blend-mode: multiply; }
        .trade-shell > :not(.nemt-art-layer):not(style) { position: relative; z-index: 1; }
        .nemt-brush { position: absolute; display: block; filter: saturate(.9); opacity: .9; }
        .nemt-brush-a { width: 70vw; height: 110px; right: -30vw; top: 12vh; background: var(--art-red); transform: rotate(-13deg); clip-path: polygon(2% 28%,100% 0,93% 75%,8% 100%,13% 67%,0 56%); opacity: .22; }
        .nemt-brush-b { width: 78vw; height: 150px; left: -38vw; bottom: 10vh; background: var(--art-green); transform: rotate(18deg); clip-path: polygon(0 24%,95% 0,100% 58%,11% 100%,18% 64%); opacity: .18; }
        .nemt-ink { position: absolute; width: 7px; height: 7px; border-radius: 99px; background: #111; box-shadow: 18px 11px 0 2px #111, 43px -9px 0 -1px #111, 67px 26px 0 1px #111, 92px 2px 0 -2px #111; opacity: .55; }
        .nemt-ink-a { right: 11vw; top: 26vh; transform: rotate(17deg); }
        .nemt-ink-b { left: 8vw; bottom: 25vh; transform: rotate(-19deg); }
        .trade-card, .trade-card-flat, .trade-card-accent {
          background: rgba(255,252,245,.86) !important;
          border: 1px solid rgba(22,23,20,.16) !important;
          border-radius: 3px 20px 5px 15px !important;
          box-shadow: 7px 8px 0 rgba(18,63,57,.12) !important;
          backdrop-filter: blur(14px);
        }
        .trade-glass-highlight { background: transparent !important; }
        .trade-card-accent { border-top: 5px solid var(--art-green) !important; }
        .trade-input {
          color: var(--art-ink) !important; background: rgba(255,255,255,.62) !important;
          border-color: rgba(22,23,20,.24) !important; border-radius: 2px 13px 4px 10px !important;
        }
        .trade-input::placeholder { color: rgba(22,23,20,.38) !important; }
        .trade-btn { border-radius: 2px 14px 3px 10px !important; font-weight: 800 !important; letter-spacing: .04em; }
        .trade-btn-primary { background: var(--art-ink) !important; color: var(--art-paper) !important; box-shadow: 5px 5px 0 var(--art-red) !important; }
        .trade-btn-outline, .trade-quick-btn { color: var(--art-ink) !important; background: rgba(255,252,245,.72) !important; border-color: rgba(22,23,20,.25) !important; }
        .trade-chip { color: var(--art-ink) !important; background: rgba(255,252,245,.75) !important; border-color: rgba(22,23,20,.22) !important; border-radius: 2px 9px 3px 7px !important; }
        .trade-cyan, .text-cyan-300, .text-cyan-400 { color: var(--art-red) !important; }
        .text-slate-100, .text-slate-200, .text-slate-300, .text-slate-400 { color: var(--art-ink) !important; }
        .text-slate-500 { color: rgba(22,23,20,.62) !important; }
        .text-slate-600 { color: rgba(22,23,20,.42) !important; }
        .trade-number { font-family: "Arial Narrow", "Roboto Condensed", monospace !important; }
        .trade-seg { background: rgba(255,252,245,.7) !important; border: 1px solid rgba(22,23,20,.18) !important; }
        .trade-seg-btn { color: rgba(22,23,20,.5) !important; }
        .trade-seg-btn-active { color: var(--art-paper) !important; background: var(--art-green) !important; }
        .trade-bottom-nav { background: rgba(240,234,223,.92) !important; border-top: 1px solid rgba(22,23,20,.16) !important; backdrop-filter: blur(18px); }
        .trade-nav-item { color: rgba(22,23,20,.46) !important; }
        .trade-nav-item-active { color: var(--art-ink) !important; background: transparent !important; }
        .trade-nav-item-active::after { content: ""; width: 22px; height: 4px; background: var(--art-red); transform: rotate(-4deg); }
        .trade-toast { color: var(--art-paper) !important; background: var(--art-ink) !important; border-color: transparent !important; }
      `}</style>
    </>
  );
}
