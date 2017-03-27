#coding: utf-8
from jinja2 import Template, Environment, PackageLoader
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import subprocess
import sys
import os
import re

class StatisticalDesign:
	grades = ['A+','A','A-','B+','B','B-','C+','C','C-','D+','D','D-','E+','E','E-','F']
	number = re.compile("\d+\.\d*")
	tTestTemplateName = 'ttest.template'
	factorialTemplateName = 'factorial.template'
	framewise_displacement_threshold = 0.5

	@classmethod
	def createCovariates(cls, dataframe ):
		"""
		Creates covariate structure that could be used in the jinja2 template.
		"""
		#dataframe = dataframe.fillna(method=None)
		covariates = []
		for column_index,column in enumerate(dataframe.columns):
			covvalues = []
			#Specify which subject the value belong to – as a comment in the matlab vector 
			for subject_index, value in dataframe.ix[:,column_index].iteritems():
				if value is np.nan: covvalues.append("0 %{} !!! NaN !!!".format( subject_index ))
				else: covvalues.append("{} %{}".format( value, subject_index ) )
			covariate = { 'number': column_index+1, 'name': column, 'covvalues': covvalues } 
			covariates.append(covariate)
		return covariates

	@classmethod
	def help(cls):
		"""
		Prints help text.
		"""
		help_text = """Usage:
		python statistical_design.py <mode> <base_dir> <covariates_file> <exclusion_criterion> <input_files_mask>

		E.g.:
		python statistical_design.py VBM covariates.csv C+ mri/smwp1anat.nii
		python statistical_design.py fMRI covariates.csv 0.05 foiswaufunc_degCM.nii

		The covariates file:
		First column has to match the names of the subject directories.
		The second column has to be binary (zero or one) to indicate whether the subject is patient or control.
		"""
		print help_text

	@classmethod
	def getGradeIndex(cls, IQR):
		"""
		Converts a CAT12 toolbox image quality ratings (IQR) to index in marks list.
		"""
		#matlab indexes from 1, python from 0, therefore substract 2 instead of 1:
		return int( round ( (IQR * 3) - 2 ) ) 

	@classmethod
	def excludeCAT(cls, dataframe, exclusion_criterion):
		"""
		Returns a tuple of two dataframes, first is the one that survives the exclusion criterion, the other does not.
		"""
		#TODO raise error if exclusion_criterion not in cls.grades
		index = cls.grades.index( exclusion_criterion )
		toExclude = lambda iqr: True if (cls.getGradeIndex(iqr) >= index) else False
		toKeep  = lambda iqr: False if (cls.getGradeIndex(iqr) >= index) else True
		exclude = dataframe.loc[ map(toExclude, dataframe.IQR) ]
		keep    = dataframe.loc[ map(toKeep,    dataframe.IQR) ]
		return (keep, exclude)

	@classmethod
	def excludeRsFMRI(cls, dataframe, exclusion_criterion):
		"""
		Returns a tuple of two dataframes, first is the one that survives the exclusion criterion, the other does not.
		"""
		toExclude = lambda fd_ratio: True if (fd_ratio >= exclusion_criterion) else False
		toKeep  = lambda fd_ratio: False if  (fd_ratio >= exclusion_criterion) else True
		exclude = dataframe.loc[ map(toExclude, dataframe.FD_suprathreshold_ratio) ]
		keep    = dataframe.loc[ map(toKeep,    dataframe.FD_suprathreshold_ratio) ]
		return (keep, exclude)

	@classmethod
	def getGrade(cls, IQR):
		"""
		Converts a CAT12 toolbox image quality ratings (IQR) to marks (A+, A, A-, B+, B, B-, etc.).
		"""
		gradeIndex= cls.getGradeIndex( IQR )
		if gradeIndex> len(cls.grades): return 'F'
		else: return cls.grades[gradeIndex]

	@classmethod
	def parseCAT(cls, filename, path_to_quality_measure):
		"""
		Reads covariates from a csv file. Ads TIV, brain volume, gray matter, white matter, CSF and image quality rating (IQR).
		Returns a Pandas dataframe.
		"""
		covariates = pd.read_csv(filename)
		subjects = list( covariates.ix[:,0] )
		covariates = covariates.set_index( covariates.columns[0] )
		print "file;grade;TIV;GM_abs[ml];WM_abs[ml];CSF_abs[ml]"
		for subject in subjects:
			with open(subject + path_to_quality_measure) as file_handle:
				xml = file_handle.read()
				soup = BeautifulSoup(xml, 'xml')
				TIV = soup.find('subjectmeasures').find('vol_TIV').text
				absolute = soup.find('subjectmeasures').find('vol_abs_CGW').text
				relative = soup.find('subjectmeasures').find('vol_rel_CGW').text
				csf_abs, gm_abs, wm_abs = cls.number.findall(absolute)
				csf_rel, gm_rel, wm_rel = cls.number.findall(relative)

				quality = float(soup.find('qualityratings').find('IQR').text)
				grade = cls.getGrade( quality )
				covariates.set_value( subject, 'TIV', float(TIV) )
				covariates.set_value( subject, 'brain', float(gm_abs)+float(wm_abs) )
				covariates.set_value( subject, 'GM', float(gm_abs) )
				covariates.set_value( subject, 'WM', float(wm_abs) )
				covariates.set_value( subject, 'CSF', float(csf_abs) )
				covariates.set_value( subject, 'IQR', quality )

				print "{};{};{};{};{};{}".format(
					subject, grade, TIV,
					gm_abs, wm_abs, csf_abs,
				)
		return covariates

	@classmethod
	def parseRsFMRI(cls, filename, path_to_quality_measure):
		"""
		Reads covariates from a csv file. Ads percentage of framewise displacement above a threshold level.
		Returns a Pandas dataframe.
		"""
		covariates = pd.read_csv(filename)
		subjects = list( covariates.ix[:,0] )
		covariates = covariates.set_index( covariates.columns[0] )
		for subject in subjects:
			with open(subject + path_to_quality_measure) as file_handle:
				framewise_displacement = file_handle.readlines()
				framewise_displacement = map(float, framewise_displacement)
				is_above_threshold = lambda fd: 1 if fd > cls.framewise_displacement_threshold else 0
				fd_above = map(is_above_threshold, framewise_displacement)
				fd_above_ratio = sum( fd_above )/float(len(fd_above))
				covariates.set_value( subject, 'FD_suprathreshold_ratio', fd_above_ratio )
		return covariates
	@classmethod
	def generateMatlabTTestCode(cls, outputdir, studyGroup1, studyGroup2, covariatesList):
		"""
		Renders a matlab t-test code using a template and a list of covariates.
		"""
		env = Environment(loader=PackageLoader(__name__, '.'))
		template = env.get_template(cls.tTestTemplateName)
		render = template.render(
			output= outputdir + "/ttest/",
			group1=studyGroup1,
			group2=studyGroup2,
			covariates=covariatesList
		)
		if not os.path.isdir(outputdir): subprocess.call(['mkdir', outputdir])
		if not os.path.isdir(outputdir + '/ttest/'): subprocess.call(['mkdir', outputdir + '/ttest/'])
		with open(outputdir + '/ttest/design.m', 'w') as f: f.write(render)
		return render

	def generateMatlabFactorialCode(cls, outputdir, subjects, covariatesList):
		"""
		Renders a matlab factorial code using a template and a list of covariates.
		"""
		env = Environment(loader=PackageLoader(__name__, '.'))
		template = env.get_template(cls.factorialTemplateName)
		render = template.render(
			output= outputdir + "/factorial/",
			group1=studyGroup1,
			group2=studyGroup2,
			covariates=covariatesList
		)
		if not os.path.isdir(outputdir): subprocess.call(['mkdir', outputdir])
		if not os.path.isdir(outputdir + '/factorial/'): subprocess.call(['mkdir', outputdir + '/factorial/'])
		with open(outputdir + '/factorial/design.m', 'w') as f: f.write(render)
		return render

		

if __name__ == '__main__':
	if len(sys.argv) <= 2:
		StatisticalDesign.help()
		exit(1)
	else:
		if sys.argv[1] == 'VBM':
			#Get dataframe from sys.argv[1] with TIV, GM, WM, CSF and image quality measure (IQR)
			covariates = StatisticalDesign.parseCAT( sys.argv[2], '/report/cat_anat.xml' )
			print ""

			#Exclude equal to or worse than sys.argv[2]
			keep, exclude = StatisticalDesign.excludeCAT( covariates, sys.argv[3] )
			print "Exluding subject equal to or worse than {}:".format(sys.argv[3])
			print list(exclude.index)
			print "Saving to VBM_subjects_to_keep.csv and VBM_subjects_to_exclude.csv"
			keep.to_csv('VBM_subjects_to_keep.csv')
			exclude.to_csv('VBM_subjects_to_exclude.csv')

			#Groups:
			path = os.path.dirname(os.path.abspath(__file__)) + '/{}/' + sys.argv[4]
			dirbase = os.path.dirname(os.path.abspath(__file__))
			group1Value = keep.ix[0,0]
			group1DF = keep.loc[ keep.ix[:,0] == group1Value ]
			group1 = [ path.format(name) for name in group1DF.index ]
			group2DF = keep.loc[ keep.ix[:,0] != group1Value ]
			group2 = [ path.format(name) for name in group2DF.index ]
			subjects = [ path.format(name) for name in keep.index ]

			#Generate matlab code for statistical design with a template
			covariatesList = StatisticalDesign.createCovariates(keep)
			matlabTTestCode = StatisticalDesign.generateMatlabTTestCode(dirbase + '/structural', group1, group2, covariatesList)
			print matlabTTestCode
			print "*"*30
			print ""
			
			matlabFactorialCode = StatisticalDesign.generateMatlabFactorialCode(dirbase + '/structural', subjects, covariatesList)
			print matlabCode
		if sys.argv[1] == 'fMRI':
			#Get dataframe from sys.argv[1] with ratio of frames whose framewise displacement exceeds the threshold level
			covariates = StatisticalDesign.parseRsFMRI( sys.argv[2], '/framewise_displacement.txt' )
			print ""

			#Exclude equal to or worse than sys.argv[2]
			keep, exclude = StatisticalDesign.excludeRsFMRI( covariates, sys.argv[3] )
			print "Exluding subject equal to or worse than {}:".format(sys.argv[3])
			print list(exclude.index)
			print "Saving to rsfMRI_subjects_to_keep.csv and rsfMRI_subjects_to_exclude.csv"
			keep.to_csv('rsfMRI_subjects_to_keep.csv')
			exclude.to_csv('rsfMRI_subjects_to_exclude.csv')

			#Groups:
			path = os.path.dirname(os.path.abspath(__file__)) + '/{}/' + sys.argv[4]
			dirbase = os.path.dirname(os.path.abspath(__file__))
			group1Value = keep.ix[0,0]
			group1DF = keep.loc[ keep.ix[:,0] == group1Value ]
			group1 = [ path.format(name) for name in group1DF.index ]
			group2DF = keep.loc[ keep.ix[:,0] != group1Value ]
			group2 = [ path.format(name) for name in group2DF.index ]
			subjects = [ path.format(name) for name in keep.index ]

			#Generate matlab code for statistical design with a template
			covariatesList = StatisticalDesign.createCovariates(keep)
			matlabTTestCode = StatisticalDesign.generateMatlabTTestCode(dirbase + '/functional', group1, group2, covariatesList)
			print matlabTTestCode
			print "*"*30
			print ""
			
			matlabFactorialCode = StatisticalDesign.generateMatlabFactorialCode(dirbase + '/functional', subjects, covariatesList)
			print matlabCode
