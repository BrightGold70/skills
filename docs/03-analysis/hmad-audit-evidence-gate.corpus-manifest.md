# hmad-audit-evidence-gate — corpus manifest

**Generated:** 2026-09-07 · **Source:** `~/.h-mad-corpora/evidence-gate/` (outside any repo)

The corpus this pins is the calibration evidence for the evidence-existence check
(#27), which `h_mad_audit_gate.py:178` REFUSED by measurement — it records that no
span-occurrence rule discriminates, and says to revisit only once a `quote:`-contract
corpus exists. A refusal is only as durable as the evidence behind it: lose the
corpus and the refusal cannot be re-verified, so the next session either re-derives
it or re-opens #27 and measures from scratch.

**This manifest is not a backup.** It makes loss DETECTABLE and the corpus
RE-DERIVABLE. Backup status measured 2026-09-07: Time Machine reports
`[Included] /Users/kimhawk/.h-mad-corpora`, but `tmutil latestbackup` fails with
`Failed to mount destination` (error 18), so no backup could be verified. Included
is not backed up, and "I could not check" is not "it is safe".

Re-derive a lost prompt: each `audit_gc_<phase>_c<N>_<leg>.txt` is the assembled
audit prompt for HemaSuite `#18 gateway-consolidation` at that cycle and leg. Rebuild
with `h_mad_assemble_audit.py` against that cycle's commit in
`/Users/kimhawk/orca/HemaSuite/hematology-paper-writer`; the measurement doc
(`hmad-audit-evidence-gate.measurement.md:110-111`) names the corpus and the two
scripts as the durable artifacts.

Verify every file still matches:

The manifest path is ABSOLUTE on purpose: the `cd` moves you out of the repo, so a
repo-relative path resolves to nothing and `grep` reports a missing file rather than
a mismatch. Measured — the first version of this block was written relative and
returned no rows.

```bash
M=/Users/kimhawk/orca/skills/docs/03-analysis/hmad-audit-evidence-gate.corpus-manifest.md
cd ~/.h-mad-corpora/evidence-gate
grep '^| `' "$M" \
  | sed 's/^| `//; s/` | /  /; s/ | `/  /; s/` |$//' \
  | awk '{print $3"  "$1}' | shasum -a 256 -c -
```

Executed 2026-09-07 at generation: **66 of 66 `OK`**, zero mismatches, against 66
files on disk.

| file | bytes | sha256 |
|---|---:|---|
| `measure_spans.py` | 4407 | `9a98a549cab71edacfa9234911ad9b0dc964c6a98b05a1fb3a59614b7a27735e` |
| `measure_spans2.py` | 5506 | `5e9d5bfb9ea6f75a6313650757adb3cfa074ab530e20d46ccddb3d92b22af551` |
| `prompts/audit_gc_design_c45_agy.txt` | 289094 | `a5b76d5fc955dcb94277bf8506fd1268634a78f5b54d3cc9b61a48607dcf2bbc` |
| `prompts/audit_gc_design_c45_codex.txt` | 289098 | `296e9473fac1969c9c4ea20740978320a1115d080db9e9a8ec91feac7727975b` |
| `prompts/audit_gc_design_c46_agy.txt` | 291728 | `c07015f109fb4c5b0dd3b34c9b4a7d247f4fda43992b8f7fcccfb8715a19c8ff` |
| `prompts/audit_gc_design_c46_codex.txt` | 291732 | `bc3f96c6afe4f064018cb6ba3b8a154564fdd5dfd4fbeb4f3c13298c5b6e7b03` |
| `prompts/audit_gc_design_c47_agy.txt` | 292809 | `053b04b069d1fe188cbe306b48cadf7cb68ebe496196747e99345434bcea55b8` |
| `prompts/audit_gc_design_c47_codex.txt` | 292813 | `f603a51e1d55a8ccb6d92c193c49172ca2f09ce3a4d1e694795f28fd75d105a4` |
| `prompts/audit_gc_design_c48_agy.txt` | 294398 | `fbc1245117e2f94b707b477a45727b066a1b4d132b0fddc97dee6e8ecc7a0cf1` |
| `prompts/audit_gc_design_c48_codex.txt` | 294402 | `67959c6141ca9d5b87340c5284ae8bea70cae1330a7681f5b3fb071a66c431ce` |
| `prompts/audit_gc_design_c49_agy.txt` | 295025 | `5d43ea0ff718601ac40dbbed045cd014ce80e02e146ea886c83d0803558f8112` |
| `prompts/audit_gc_design_c49_codex.txt` | 295029 | `4f9c58a4abea93ee49ba7ed50e0a73eb23bbf2f772690f937fbc5bc43e96185b` |
| `prompts/audit_gc_design_c50_agy.txt` | 299844 | `72a9022ec24a9a44b5815d169c744639f1427745aed2aa4b0f39116d7c2670b0` |
| `prompts/audit_gc_design_c50_codex.txt` | 299848 | `d0ae74cd67f02917269fda0a7ea041adab5ca65b46c4157ab8e7cb4beb9e1baa` |
| `prompts/audit_gc_design_c51_agy.txt` | 303384 | `08d172dbaea5919ff1aba4fffb3bc6f772e0292a4025811989bffcc940ea18cd` |
| `prompts/audit_gc_design_c51_codex.txt` | 303388 | `17a772eee784e2f1d96c5ad75f829e8e36421829d1ba9bb0a415a5df7caa89ee` |
| `prompts/audit_gc_design_c52_agy.txt` | 306370 | `d96e28f60753d60688cb171007f0ad27bcf95d1175e704bec099dd9619569a9b` |
| `prompts/audit_gc_design_c52_codex.txt` | 306374 | `f9b52a7af16f53e251d5240e086bd8b0de9ad46e67d317868837b22ee42688b3` |
| `prompts/audit_gc_design_c53_agy.txt` | 308508 | `1be32aa14a93b59e3b2c67a21b5ddbe1d591056ccac66279761599fd7ee03fe0` |
| `prompts/audit_gc_design_c53_codex.txt` | 308512 | `9d8c54b544f586755e36fd5a8b913c336f87af60aede26940a8e6f0250b73780` |
| `prompts/audit_gc_design_c54_agy.txt` | 311676 | `b0faf3300d891454a21a963390a21c9f9c1a8585f960ba33cddb0c68973952ca` |
| `prompts/audit_gc_design_c54_codex.txt` | 311680 | `118e114f6975f7e3134df307b6b0058c6c7e75493f5907abcb594f6d53b1e638` |
| `prompts/audit_gc_design_c55_agy.txt` | 316081 | `367f45ad9179845bb21be3acf41f0584c2321a1475e8d4016fd18e730feb365b` |
| `prompts/audit_gc_design_c55_codex.txt` | 316085 | `a68f1144a49c6561ace7877fdad7124e7520806ed3bb867e3db78b07c9f0b898` |
| `prompts/audit_gc_design_c56_agy.txt` | 317510 | `84db182482cd736ae340a0e26e22c9289dd329f6efd38ca5ba741ff6eeffe16b` |
| `prompts/audit_gc_design_c56_codex.txt` | 317514 | `eb812cea8c7e95792948be906b7746f589bd686ca141bb323042761d3c1e25bf` |
| `prompts/audit_gc_design_c57_agy.txt` | 322646 | `e7320afa2901b84f3f2ef719066077d6a14db0a7359a821b6451f71253dd44bd` |
| `prompts/audit_gc_design_c57_codex.txt` | 322650 | `1a97b84303b06cd704f13d2e3fcee12271622930f739affdd5c1684daed93110` |
| `prompts/audit_gc_design_c58_agy.txt` | 325052 | `83843112001fb66e64952c62ea2313a698bcc7aed1869bedb2c3ea44c700cd5b` |
| `prompts/audit_gc_design_c58_codex.txt` | 325056 | `ca36f2c476f19582d992d9e119c20d3e3a7a06c406c9b663626849515d4916a1` |
| `prompts/audit_gc_design_c59_agy.txt` | 326946 | `913f002ea47398ead8bc0aecaa3c21309525828aa14f0f3d1194856a4f946186` |
| `prompts/audit_gc_design_c59_codex.txt` | 326950 | `3a3fb414883584e3223a9ee3f74e91285b00dc907b70ee4cbed895c46fbf7232` |
| `prompts/audit_gc_design_c60_agy.txt` | 326946 | `f86cc5ebfd9f25abaa8d79995c4e5bc2b50a3baeb4f6a1209000c194c976b23f` |
| `prompts/audit_gc_design_c60_codex.txt` | 326950 | `6d717a428b04c71237c29f13cf209f7555d5bfd11c22fc47cb38f8eacb4996d1` |
| `prompts/audit_gc_design_c61_agy.txt` | 331736 | `41925343a6532e830e0cb1f89308431312860c117dd063bf7455040b7bcd0760` |
| `prompts/audit_gc_design_c61_codex.txt` | 331740 | `1b2f6b02a7faacc05dfcc95dcdd507096cecc445709fa587ceb4036a0df88830` |
| `prompts/audit_gc_design_c62_agy.txt` | 333156 | `c5d90f309ae4b3124bb1067d24003d85ef9a28ee78c0fc80095de2e7de05dc8c` |
| `prompts/audit_gc_design_c62_codex.txt` | 333160 | `68d5995bb904472d98c0d024251886cd0b8059544671f427b30fe5ec8de59e58` |
| `prompts/audit_gc_design_c63_agy.txt` | 333806 | `f1d6e9545381c97cfba5f4d2ec889b084f9f40add72e4bb88a786e2a3b747b70` |
| `prompts/audit_gc_design_c63_codex.txt` | 333810 | `8efaa288bb29329b4556db5f61b95468f1e4f930d828fab30f92add981864258` |
| `prompts/audit_gc_design_c64_agy.txt` | 336190 | `da771fa524109278218fd6f59046da9c02cdb0b57b1ab8abcece9c99b333095c` |
| `prompts/audit_gc_design_c64_codex.txt` | 336194 | `3007ff249f98b560c6af6acdf4317d0140a597912ce2080d6995219b94aa7166` |
| `prompts/audit_gc_design_c65_agy.txt` | 337823 | `013400b084a5a6251f0e2826c2f4ab90ea9ea92678f00fb4599ec6db33884517` |
| `prompts/audit_gc_design_c65_codex.txt` | 337827 | `7ad10c211cece2c312bd7a1d3973046bf6328dfa490b5466f90a4f9dc8d84d1a` |
| `prompts/audit_gc_design_c66_agy.txt` | 337823 | `57475727a2028b42564e0efe8728dd29f8fbdaef5ef23b9d9c380b5e8b870a80` |
| `prompts/audit_gc_design_c66_codex.txt` | 337827 | `6546ead0c8dee79bcf94fbaf601bb885ece373c41bb15fbe2e7a36d1d2b01336` |
| `prompts/audit_gc_design_c67_agy.txt` | 338409 | `6456df06ce03ebbd00a7df36c17bb1a34aee843f3d52c5784c48b659549ac505` |
| `prompts/audit_gc_design_c67_codex.txt` | 338413 | `63886e8fa547dd4ce008d696cf04cda64281b829d360a04023823aa3d29a5397` |
| `prompts/audit_gc_design_c68_agy.txt` | 340059 | `202ae0f1e9f2d622c390869171b9e6d3d19db773e107e1a73e5ee41232f157ad` |
| `prompts/audit_gc_design_c68_codex.txt` | 340063 | `8fb30034578c54773b9825e9fbc14ec9be403a6b14a0165303f6ddefb6b50ffc` |
| `prompts/audit_gc_design_c69_agy.txt` | 341172 | `7c2f868a04f848e0c734a80e66cf9936492213628a9665cd559b6833d4384d02` |
| `prompts/audit_gc_design_c69_codex.txt` | 341176 | `9bb64150949c3c8e0d5910e08e88b56aeb01e07cbb51c9f51c445afc8d4bd4f4` |
| `prompts/audit_gc_design_c70_agy.txt` | 342814 | `b97f24f1136e6993bcf5cf267d1cac3cf994e4d8e8998bf180dd1f3d255e8891` |
| `prompts/audit_gc_design_c70_codex.txt` | 342818 | `826fc14e86076640ed0a2defc98c5c97df718ce6004f1388c469ca3cbef971bd` |
| `prompts/audit_gc_design_c71_agy.txt` | 342814 | `3338ce0e0c60e6627b73f0ebd2589708ef577110705f7c6c729e5d7d3ee39d3e` |
| `prompts/audit_gc_design_c71_codex.txt` | 342818 | `8ca3ba70b894b96e2a92e825f06b4e3be16eee8e791be37316243b041ae4cda8` |
| `prompts/audit_gc_design_c72_agy.txt` | 344950 | `7d37c2606be0a02daac002bfd5bf5e6f4c3446189573c7a0683e619bb176af70` |
| `prompts/audit_gc_design_c72_codex.txt` | 344954 | `e098546b95dd5da1e127198434e84af02779fa884194093b02940d6ade9fc08c` |
| `prompts/audit_gc_design_c73_agy.txt` | 346348 | `0cc5fae4cd60a9b1a5316e871c52711e00e4e0e0e5856c97886d679638d008db` |
| `prompts/audit_gc_design_c73_codex.txt` | 346352 | `5c7bd0aca31f73f208d9ec0b3008526153db0651f698957bff284139d417d364` |
| `prompts/audit_gc_design_c74_agy.txt` | 346348 | `b831648336b88ae763cb87b12d478b2ae8248e3f4bc3afb7cb648aa8b84e3220` |
| `prompts/audit_gc_design_c74_codex.txt` | 346352 | `ea0e8692111d51ef21310e0ef92b4f4c7250d6db474804094b04149ed9ef4f11` |
| `prompts/audit_gc_design_c75_agy.txt` | 346721 | `df2df285600d405394848bb2659cd310a24cc365545f3b7650e13f7a7d6b5618` |
| `prompts/audit_gc_design_c75_codex.txt` | 346725 | `bab1123d8ebf4c021775413267474491b5f3fba4d8f63f0aae81c7ac12fc0699` |
| `prompts/audit_gc_design_c76_agy.txt` | 346721 | `2054cd7556fe612a81b0b3015ea8f0ed257559763a50fb3a848bde1086f3fdb1` |
| `prompts/audit_gc_design_c76_codex.txt` | 346725 | `e9750fd97f13ff448d54c6cbbd67069f35c0b60ce278eabe1c715c0c5689d2ee` |
