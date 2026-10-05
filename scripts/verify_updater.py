"""Updater integrity check.

Verifies the invariant the stable client depends on:

    for every entry in metadata.json,
    md5(unzip(download(name + ".zip"))) == file_hashmd5

Why this exists as a script rather than a unit test: the failure it catches is
*invisible at the origin*. The updater serves a well-formed zip containing
well-formed old bytes, and the client logs only that it downloaded a file
successfully. The symptom is a permanent "update available" loop that re-downloads
the whole set on every check. Nothing anywhere reports a problem, so it needs an
explicit assertion -- see `notes.md` (findings-3/4).

Run manually, or from CI immediately after the publish step:

    python updater-service/scripts/verify_updater.py

Exits non-zero on any mismatch or edge-cached client zip. Read-only: it only ever
issues GET/HEAD.
"""

from __future__ import annotations

import hashlib
import io
import sys
import zipfile

import httpx

DEFAULT_BASE = "https://updater.041095.xyz"
CLIENT_PREFIX = "resources/client"

# Assemblies the stable client cannot start a multiplayer lobby without.
#
# This is the MessagePack 2.5 runtime closure for .NET Framework 4.8, plus the
# corelib packages it drags in. `System.Buffers` is the one that was missing, and
# it fails in the worst possible way: MessagePack's serialization buffers
# (`ArrayPool`, `IBufferWriter`, `ReadOnlySequence`) live there, and
# `MessagePackSecurity` touches them during *static initialisation*, so the only
# symptom is a cascade of `TypeInitializationException` the first time a player
# presses create. Nothing about the manifest being otherwise valid hints at it.
#
# A manifest consistency check cannot see this -- every entry it inspects hashes
# correctly whether or not a dependency was ever uploaded -- so the closure is
# asserted by name as its own check.
MPV2_RUNTIME_ASSEMBLIES = (
    "MessagePack.dll",
    "MessagePack.Annotations.dll",
    "Microsoft.Bcl.AsyncInterfaces.dll",
    "System.Buffers.dll",
    "System.Memory.dll",
    "System.Numerics.Vectors.dll",
    "System.Runtime.CompilerServices.Unsafe.dll",
    "System.Threading.Tasks.Extensions.dll",
)


def verify(base: str = DEFAULT_BASE, *, verbose: bool = True) -> int:
    """Return the number of failures (0 == healthy)."""
    # the updater 403s the default httpx/urllib user-agent
    http = httpx.Client(timeout=300, follow_redirects=True, headers={"User-Agent": "refx-updater-verify/1.0"})

    meta = http.get(f"{base}/metadata.json").json()

    if verbose:
        print(f"{len(meta)} entries in metadata.json\n")

    failures: list[str] = []
    edge_cached: list[str] = []

    published = {entry["filename"] for entry in meta}
    missing_runtime = [name for name in MPV2_RUNTIME_ASSEMBLIES if name not in published]

    if missing_runtime:
        failures.append(
            "MPV2 runtime closure incomplete, the client will fail at lobby create: "
            + ", ".join(missing_runtime)
        )

    for entry in meta:
        name = entry["filename"]
        expected = entry["file_hashmd5"]

        headers = http.head(f"{base}/{CLIENT_PREFIX}/{name}.zip").headers
        cf_status = headers.get("cf-cache-status", "?")

        # A HIT on this path is a bug regardless of whether the bytes happen to be
        # right: the URL is mutable, so the cache can serve a stale object at any
        # moment and there is no origin header to stop it.
        if cf_status == "HIT":
            edge_cached.append(name)

        raw = http.get(f"{base}/{CLIENT_PREFIX}/{name}.zip").content

        try:
            with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                inner = archive.read(name)
        except Exception as exc:  # noqa: BLE001 - any failure here is a finding
            failures.append(f"{name}: unzip failed: {exc}")
            continue

        got = hashlib.md5(inner).hexdigest()
        ok = got == expected

        if not ok:
            failures.append(f"{name}: md5 {got} != manifest {expected}")
        elif cf_status == "HIT":
            failures.append(f"{name}: correct bytes but served from edge cache (HIT)")

        if verbose:
            print(f"  {'OK ' if ok else 'BAD'} cf={cf_status:8} {name}")

    if verbose:
        print(f"\nchecked {len(meta)}, failures {len(failures)}, edge-cached {len(edge_cached)}")

        if edge_cached:
            print("  edge-cached client zips:", ", ".join(edge_cached))

        for line in failures:
            print(f"  FAIL {line}")

    return len(failures)


def main() -> int:
    base = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_BASE
    failures = verify(base)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
