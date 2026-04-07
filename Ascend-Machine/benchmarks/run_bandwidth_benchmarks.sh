#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
ROOT_DIR=$(cd -- "$SCRIPT_DIR/.." && pwd)
RUN_ID=${1:-$(date +%Y%m%d_%H%M%S)}
OUT_DIR="$ROOT_DIR/results/$RUN_ID"
BUILD_DIR="$ROOT_DIR/build"
HCCL_BUILD_DIR="$BUILD_DIR/hccl_test"
ACL_BENCH_BIN="$BUILD_DIR/acl_copy_bench"
NUMA_MEMCPY_BIN="$BUILD_DIR/numa_memcpy_bench"
FIO_FILE=${FIO_FILE:-/data/ascend_machine_nvme_bw.bin}
MPI_HOME=${MPI_HOME:-/usr/lib/aarch64-linux-gnu/openmpi}
ASCEND_TOOLKIT_HOME=${ASCEND_TOOLKIT_HOME:-/usr/local/Ascend/ascend-toolkit/latest}
ASCEND_HCCL_SRC=${ASCEND_HCCL_SRC:-$ASCEND_TOOLKIT_HOME/tools/hccl_test}
NPU_SMI_BIN=${NPU_SMI_BIN:-/home/shuhao/.local/bin/npu-smi}
CLEAN_ENV_PATH="$ASCEND_TOOLKIT_HOME/bin:$ASCEND_TOOLKIT_HOME/compiler/ccec_compiler/bin:$ASCEND_TOOLKIT_HOME/tools/ccec_compiler/bin:/usr/bin:/usr/sbin:/bin:/sbin"
CLEAN_ENV_LD_LIBRARY_PATH="$ASCEND_TOOLKIT_HOME/lib64:$ASCEND_TOOLKIT_HOME/lib64/plugin/opskernel:$ASCEND_TOOLKIT_HOME/lib64/plugin/nnengine:$ASCEND_TOOLKIT_HOME/opp/built-in/op_impl/ai_core/tbe/op_tiling/lib/linux/$(arch):$ASCEND_TOOLKIT_HOME/tools/aml/lib64:$ASCEND_TOOLKIT_HOME/tools/aml/lib64/plugin:/usr/local/Ascend/driver/lib64:/usr/local/Ascend/driver/lib64/common:/usr/local/Ascend/driver/lib64/driver"

mkdir -p "$OUT_DIR"
ln -sfn "$RUN_ID" "$ROOT_DIR/results/latest"

export ASCEND_TOOLKIT_HOME
export LD_LIBRARY_PATH="$ASCEND_TOOLKIT_HOME/lib64:$ASCEND_TOOLKIT_HOME/lib64/plugin/opskernel:$ASCEND_TOOLKIT_HOME/lib64/plugin/nnengine:$ASCEND_TOOLKIT_HOME/opp/built-in/op_impl/ai_core/tbe/op_tiling/lib/linux/$(arch):$ASCEND_TOOLKIT_HOME/tools/aml/lib64:$ASCEND_TOOLKIT_HOME/tools/aml/lib64/plugin:${LD_LIBRARY_PATH:-}"
export PYTHONPATH="$ASCEND_TOOLKIT_HOME/python/site-packages:$ASCEND_TOOLKIT_HOME/opp/built-in/op_impl/ai_core/tbe:${PYTHONPATH:-}"
export PATH="$ASCEND_TOOLKIT_HOME/bin:$ASCEND_TOOLKIT_HOME/compiler/ccec_compiler/bin:$ASCEND_TOOLKIT_HOME/tools/ccec_compiler/bin:${PATH}"
export ASCEND_AICPU_PATH="$ASCEND_TOOLKIT_HOME"
export ASCEND_OPP_PATH="$ASCEND_TOOLKIT_HOME/opp"
export TOOLCHAIN_HOME="$ASCEND_TOOLKIT_HOME/toolkit"
export ASCEND_HOME_PATH="$ASCEND_TOOLKIT_HOME"

log() {
    printf '[%s] %s\n' "$(date '+%F %T')" "$*"
}

run_clean_env() {
    env -i \
        HOME="$HOME" \
        USER="${USER:-shuhao}" \
        LOGNAME="${LOGNAME:-shuhao}" \
        SHELL=/bin/bash \
        TERM="${TERM:-xterm-256color}" \
        PATH="$CLEAN_ENV_PATH" \
        LD_LIBRARY_PATH="$CLEAN_ENV_LD_LIBRARY_PATH" \
        ASCEND_TOOLKIT_HOME="$ASCEND_TOOLKIT_HOME" \
        ASCEND_AICPU_PATH="$ASCEND_TOOLKIT_HOME" \
        ASCEND_OPP_PATH="$ASCEND_TOOLKIT_HOME/opp" \
        TOOLCHAIN_HOME="$ASCEND_TOOLKIT_HOME/toolkit" \
        ASCEND_HOME_PATH="$ASCEND_TOOLKIT_HOME" \
        "$@"
}

capture_static_inventory() {
    log "Capturing static inventory"
    uname -a > "$OUT_DIR/uname.txt"
    hostname > "$OUT_DIR/hostname.txt"
    lscpu > "$OUT_DIR/lscpu.txt"
    numactl -H > "$OUT_DIR/numactl-H.txt"
    free -h > "$OUT_DIR/free-h.txt"
    lsmem > "$OUT_DIR/lsmem.txt"
    lsblk -a -o NAME,MAJ:MIN,SIZE,ROTA,TYPE,MOUNTPOINT,MODEL,VENDOR,SERIAL > "$OUT_DIR/lsblk.txt"
    lspci -D > "$OUT_DIR/lspci.txt"
    run_clean_env "$NPU_SMI_BIN" -v > "$OUT_DIR/npu-smi-version.txt"
    run_clean_env "$NPU_SMI_BIN" info > "$OUT_DIR/npu-smi-info.txt"
    run_clean_env "$NPU_SMI_BIN" topo -m > "$OUT_DIR/npu-smi-topo.txt"
    ip -br link > "$OUT_DIR/ip-link.txt"
    ip -br addr > "$OUT_DIR/ip-addr.txt"
    for nic in enp189s0f0 enp189s0f1 enp189s0f2 enp189s0f3 enp195s0f0np0 enp195s0f1np1 enp61s0f0 enp61s0f1 enp61s0f2 enp61s0f3 enp67s0f0np0 enp67s0f1np1; do
        {
            echo "=== $nic ==="
            ethtool "$nic" | grep -E 'Speed|Duplex|Port|Link detected' || true
            echo
        }
    done > "$OUT_DIR/ethtool-summary.txt"
}

build_numa_memcpy_bench() {
    log "Building numa_memcpy_bench"
    g++ -O3 -std=c++17 "$SCRIPT_DIR/numa_memcpy_bench.cpp" -lpthread -o "$NUMA_MEMCPY_BIN"
}

run_memcpy_case() {
    local name=$1
    local cpu_node=$2
    local mem_node=$3
    log "Running memcpy case $name"
    numactl --cpunodebind="$cpu_node" --membind="$mem_node" "$NUMA_MEMCPY_BIN" --threads 24 --size-mb 256 --warmup 3 --iters 20 > "$OUT_DIR/$name.memcpy.txt"
}

run_mbw_case() {
    local name=$1
    local cpu_node=$2
    local mem_node=$3
    local size_mb=$4
    log "Running mbw case $name"
    numactl --cpunodebind="$cpu_node" --membind="$mem_node" mbw -n 3 "$size_mb" > "$OUT_DIR/$name.mbw.txt"
}

prepare_fio_file() {
    log "Preparing fio file at $FIO_FILE"
    mkdir -p "$(dirname -- "$FIO_FILE")"
    sudo /usr/bin/fio \
        --name=prepare \
        --filename="$FIO_FILE" \
        --rw=write \
        --bs=1M \
        --iodepth=32 \
        --ioengine=libaio \
        --direct=1 \
        --size=16G \
        --numjobs=1 \
        --group_reporting \
        --output-format=json \
        > "$OUT_DIR/fio-prepare.json"
}

run_fio_read() {
    log "Running fio sequential read"
    sudo numactl --cpunodebind=4 --membind=4 /usr/bin/fio \
        --name=seqread \
        --filename="$FIO_FILE" \
        --rw=read \
        --bs=1M \
        --iodepth=32 \
        --ioengine=libaio \
        --direct=1 \
        --size=16G \
        --runtime=20 \
        --time_based=1 \
        --numjobs=1 \
        --group_reporting \
        --output-format=json \
        > "$OUT_DIR/fio-seqread.json"
}

build_acl_copy_bench() {
    log "Building acl_copy_bench"
    g++ -O2 -std=c++17 \
        "$SCRIPT_DIR/acl_copy_bench.cpp" \
        -I"$ASCEND_TOOLKIT_HOME/include" \
        -L"$ASCEND_TOOLKIT_HOME/lib64" \
        -Wl,-rpath,"$ASCEND_TOOLKIT_HOME/lib64" \
        -lascendcl -lpthread \
        -o "$ACL_BENCH_BIN"
}

run_acl_copy_cases() {
    log "Running ACL H2D/D2H cases"
    run_clean_env "$ACL_BENCH_BIN" --mode d2h --devices 4 --size-mb 1024 --warmup 5 --iters 20 --affinity-lists 0-23 > "$OUT_DIR/acl-copy-single-d2h.txt"
    run_clean_env "$ACL_BENCH_BIN" --mode h2d --devices 4 --size-mb 1024 --warmup 5 --iters 20 --affinity-lists 0-23 > "$OUT_DIR/acl-copy-single-h2d.txt"
    run_clean_env "$ACL_BENCH_BIN" --mode h2d --devices 4,5 --size-mb 1024 --warmup 5 --iters 20 --affinity-lists 0-23/0-23 > "$OUT_DIR/acl-copy-dual-h2d.txt"
    run_clean_env "$ACL_BENCH_BIN" --mode h2d --devices 0,1,2,3,4,5,6,7 --size-mb 512 --warmup 5 --iters 20 --affinity-lists 144-167/144-167/96-119/96-119/0-23/0-23/48-71/48-71 > "$OUT_DIR/acl-copy-all8-h2d.txt"
}

build_hccl_test() {
    log "Building hccl_test"
    rm -rf "$HCCL_BUILD_DIR"
    cp -rL "$ASCEND_HCCL_SRC" "$HCCL_BUILD_DIR"
    make -C "$HCCL_BUILD_DIR" \
        MPI_HOME="$MPI_HOME" \
        ASCEND_DIR="$ASCEND_TOOLKIT_HOME" \
        LIBS="-L${ASCEND_TOOLKIT_HOME}/lib64 -lhccl -L${ASCEND_TOOLKIT_HOME}/lib64 -lascendcl -L${MPI_HOME}/lib -lmpi -lmpi_cxx"
}

run_hccl_case() {
    local binary=$1
    local outfile=$2
    local extra_args=()
    shift 2
    if (($# > 0)); then
        extra_args=("$@")
    fi
    log "Running hccl case $binary"
    run_clean_env mpirun --bind-to none -n 8 "$HCCL_BUILD_DIR/bin/$binary" -b 64M -e 64M -i 0 -p 8 -d fp32 -n 5 -w 2 -c 0 "${extra_args[@]}" > "$OUT_DIR/$outfile"
}

run_hccl_cases() {
    run_hccl_case all_gather_test hccl-all-gather.txt
    run_hccl_case reduce_scatter_test hccl-reduce-scatter.txt
    run_hccl_case scatter_test hccl-scatter.txt -r 0
    run_hccl_case alltoall_test hccl-alltoall.txt
    run_hccl_case all_reduce_test hccl-all-reduce.txt -o sum
    run_hccl_case broadcast_test hccl-broadcast.txt -r 1
    run_hccl_case reduce_test hccl-reduce.txt -r 1 -o sum
}

main() {
    capture_static_inventory
    build_numa_memcpy_bench
    run_memcpy_case local-ddr-node0 0 0
    run_memcpy_case same-socket-remote-node1 0 1
    run_memcpy_case cross-socket-remote-node4 0 4
    run_mbw_case local-ddr-node0 0 0 4096
    run_mbw_case same-socket-remote-node1 0 1 4096
    run_mbw_case cross-socket-remote-node4 0 4 4096
    prepare_fio_file
    run_fio_read
    build_acl_copy_bench
    run_acl_copy_cases
    build_hccl_test
    run_hccl_cases
    log "Results written to $OUT_DIR"
}

main "$@"