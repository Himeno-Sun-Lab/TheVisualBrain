#!/bin/bash

#SBATCH --job-name=neuron-vizu
#SBATCH --cpus-per-task=16
#SBATCH --mem=32G
#SBATCH --array=1-20
#SBATCH --partition=prio
#SBATCH --output=out-err/_job_%j.out
#SBATCH --error=out-err/_job_%j.err


nFramesFrom=0
nFramesTo=10


nFramesNodeStart=$(($nFramesFrom+$SLURM_ARRAY_TASK_ID - 1))
nFramesNodeEnd=${nFramesTo}
nFramesStep=$SLURM_ARRAY_TASK_MAX
nNodeIndex=$SLURM_ARRAY_TASK_ID

./run-script-v2.sh $1 $2 $nFramesNodeStart $nFramesNodeEnd $nFramesStep $nNodeIndex

