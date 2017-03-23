#!/bin/bash

output_dir=../NIfTI
input_dir=.

if [ ! -d $output_dir ]; then
	mkdir $output_dir
fi
if [ ! -d $output_dir/t1 ]; then
	mkdir $output_dir/t1
fi
if [ ! -d $output_dir/rs ]; then
	mkdir $output_dir/rs
fi

Convert_raw () {
	echo "$1->$2" | tee -a $output_dir/log.txt
	if [ ! -d $output_dir/$2/ ]; then
		echo "Creating $output_dir/$2/"
		mkdir $output_dir/$2/
	fi
	
	echo Converting files in $input_dir/$1/$3/
	dcm2nii -d y -e y -i y -o $output_dir/$2/ -p y -y -v $input_dir/$1/$3/* | tee -a $output_dir/log.txt
	echo "\n\n\n" | tee -a $output_dir/log.txt

	# Siemens structure
	if [ -f $output_dir/$2/co*t1*s007a*.nii.gz ]; then
		#T1_MPRAGE_TRA_P2_ISO_1_0
		cp -v $output_dir/$2/co*t1*s007a*.nii.gz $output_dir/t1/$2_t1.nii.gz | tee -a $output_dir/log
	elif [ -f $output_dir/$2/co*t1*s008a*.nii.gz ]; then
		#T1_MPRAGE_TRA_P2_ISO_1_0
		cp -v $output_dir/$2/co*t1*s008a*.nii.gz $output_dir/t1/$2_t1.nii.gz | tee -a $output_dir/log
	elif [ -f $output_dir/$2/co*t1*s012a*.nii.gz ]; then
		#T1_MPRAGE_TRA_P2_ISO_1_0
		cp -v $output_dir/$2/co*t1*s012a*.nii.gz $output_dir/t1/$2_t1.nii.gz | tee -a $output_dir/log
	elif [ -f $output_dir/$2/co*t1*s014a*.nii.gz ]; then
		#T1_MPRAGE_TRA_P2_ISO_1_0
		cp -v $output_dir/$2/co*t1*s014a*.nii.gz $output_dir/t1/$2_t1.nii.gz | tee -a $output_dir/log
	elif [ -f $output_dir/$2/co*t1*s021a*.nii.gz ]; then
		#T1_MPRAGE_SAG_P2_ISO_1_0
		cp -v $output_dir/$2/co*t1*s021a*.nii.gz $output_dir/t1/$2_t1.nii.gz | tee -a $output_dir/log
	else
		echo "********T1 SEQUENCE NOT FOUND FOR $1********" | tee -a $output_dir/log.txt
	fi

	cp -v $output_dir/$2/*resting*.nii.gz $output_dir/rs/$2_rs.nii.gz | tee -a $output_dir/log.txt
}

Convert_ima () {
	echo "$1->$2" | tee -a $output_dir/log.txt
	if [ ! -d $output_dir/$2/ ]; then
		echo "Creating $output_dir/$2/"
		mkdir $output_dir/$2/
	fi
	
	for d in $input_dir/$1/$3/*
	do
		echo Converting files in $d
		dcm2nii -d y -e y -i y -o $output_dir/$2/ -p y -y -v $d/* | tee -a $output_dir/log.txt
		echo "\n\n\n" | tee -a $output_dir/log.txt
	done

	# Siemens structure
	if [ -f $output_dir/$2/co*t1*s007a*.nii.gz ]; then
		#T1_MPRAGE_TRA_P2_ISO_1_0
		cp -v $output_dir/$2/co*t1*s007a*.nii.gz $output_dir/t1/$2_t1.nii.gz | tee -a $output_dir/log
	elif [ -f $output_dir/$2/co*t1*s008a*.nii.gz ]; then
		#T1_MPRAGE_TRA_P2_ISO_1_0
		cp -v $output_dir/$2/co*t1*s008a*.nii.gz $output_dir/t1/$2_t1.nii.gz | tee -a $output_dir/log
	elif [ -f $output_dir/$2/co*t1*s012a*.nii.gz ]; then
		#T1_MPRAGE_TRA_P2_ISO_1_0
		cp -v $output_dir/$2/co*t1*s012a*.nii.gz $output_dir/t1/$2_t1.nii.gz | tee -a $output_dir/log
	elif [ -f $output_dir/$2/co*t1*s014a*.nii.gz ]; then
		#T1_MPRAGE_TRA_P2_ISO_1_0
		cp -v $output_dir/$2/co*t1*s014a*.nii.gz $output_dir/t1/$2_t1.nii.gz | tee -a $output_dir/log
	elif [ -f $output_dir/$2/co*t1*s021a*.nii.gz ]; then
		#T1_MPRAGE_SAG_P2_ISO_1_0
		cp -v $output_dir/$2/co*t1*s021a*.nii.gz $output_dir/t1/$2_t1.nii.gz | tee -a $output_dir/log
	else
		echo "********T1 SEQUENCE NOT FOUND FOR $1********" | tee -a $output_dir/log.txt
	fi
	cp -v $output_dir/$2/*resting*.nii.gz $output_dir/rs/$2_rs.nii.gz | tee -a $output_dir/log.txt
}

############
# Subjects #
############

Convert_raw LASTNAME_FIRSTNAME pss01 09.05.2014
Convert_ima LASTNAME_FIRSTNAME_NUMBER css06 EXPERIMENTALNI_NAME_NUMBER

##########
## Tests #
##########

echo "Final tests..." | tee -a $output_dir/log.txt
for x in $output_dir/rs/*; do echo $x; fslhd $x | grep dim4 | tee -a $output_dir/log.txt ; done | more
for x in $output_dir/t1/*; do echo $x; fslhd $x | grep slice | tee -a $output_dir/log.txt ; done | more
