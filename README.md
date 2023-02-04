# tutor_matching
This is a python program for matching students to tutors. The file has some existing rules as decided by the 2021/2022 Tutoring Chair of MIT's TBP Chapter. The rules can be changed and modified to fit the needs of a tutoring service.  

# How to:
1. Start by cloning this repo
2. Once cloned, create a file named TutorResponses and another named TuteeResponses. These should be .csv files and must have the template
  as shown in the `/templates` directory. Place these two files in the `/data` directory.
3. After getting your data files loaded, go to terminal and navigate to the directory where you cloned the repo into and type the command: `python3 matching.py`.
4. Once the script finishes running, three files should be generated: `primary_matching.csv`, `unmatched_tutors.csv` and `unmatched_tutees.csv`. These csv files can alsobe converted to xlxs files
