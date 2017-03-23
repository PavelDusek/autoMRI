subject() {
	if [ ! -d $1 ]; then
		mkdir $1
	fi
	mv ${1}_rs.nii ${1}/func.nii
	mv ${1}_t1.nii ${1}/anat.nii
}

#css=control study subject
#pss=patient study subject
dirs=( css01 css02 css03 css04 css05 css06 css07 css08 css09 css10 css11 css12 css13 css14 css15 css16 css17 css18 css19 css20 css21 css22 css23 css24 css25 css26 css27 pss01 pss02 pss03 pss04 pss05 pss06 pss07 pss08 pss09 pss10 pss11 pss12 pss13 pss14 pss15 pss16 pss17 pss18 pss19 pss20 pss21 pss22 pss23 pss24 pss25 pss26 pss27 pss28 pss30 )
for s in ${dirs[@]}
do
	subject $s
done
