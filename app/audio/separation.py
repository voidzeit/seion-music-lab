"""Source separation of reference audio with Demucs (optional `separation` extra).

Audio I/O goes through librosa/soundfile instead of torchaudio: since
torchaudio 2.9 its load/save route through TorchCodec, which is fragile on
Windows. Output: one 24-bit WAV per stem (drums, bass, other, vocals).

usage: python -m app.audio.separation <audio_file> [out_dir] [--model htdemucs_ft]
"""

from __future__ import annotations

import argparse
from pathlib import Path

DEFAULT_MODEL = "htdemucs_ft"


def separate(audio_path: Path, out_dir: Path, model_name: str = DEFAULT_MODEL) -> dict[str, Path]:
    import librosa
    import soundfile as sf
    import torch
    from demucs.apply import apply_model
    from demucs.pretrained import get_model

    model = get_model(model_name)
    model.eval()
    device = "cuda" if torch.cuda.is_available() else "cpu"

    audio, _ = librosa.load(str(audio_path), sr=model.samplerate, mono=False)
    if audio.ndim == 1:
        audio = audio[None, :].repeat(2, axis=0)
    wav = torch.from_numpy(audio).float()

    # Same normalisation as the demucs CLI.
    ref = wav.mean(0)
    mean, std = ref.mean(), ref.std()
    wav = (wav - mean) / std
    with torch.no_grad():
        sources = apply_model(model, wav[None], device=device, shifts=1, split=True, overlap=0.25)[0]
    sources = sources * std + mean

    out_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for name, source in zip(model.sources, sources, strict=True):
        path = out_dir / f"{name}.wav"
        sf.write(str(path), source.cpu().numpy().T, model.samplerate, subtype="PCM_24")
        paths[name] = path
    return paths


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("audio", type=Path)
    ap.add_argument("out_dir", type=Path, nargs="?")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    args = ap.parse_args(argv)
    out_dir = args.out_dir or args.audio.parent / "stems" / args.audio.stem
    for name, path in separate(args.audio, out_dir, args.model).items():
        print(f"{name}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
