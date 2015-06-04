# pitchPrediction
***Predicting the next pitch type for MLB Pitchers -- ML models and web-based deployment***  
*UC Berkeley MIDS 2015*  
***Authors:*** *Jason Goodman, Alan Si, Joshua Lu, Zach Beaver*  

**Files**
---------
- **analysis:** Any sort of data exploration graphs, one-off analyses, model comparisons, etc.
- **data:** A place to keep a small local training/test dataset for initial model building.
- **demo:** Back-end app, front-end application, scouting report generator, etc.
- **logs:** Logs...
- **models:** Place to save pickled sklearn models?
- **orig_R_code:** Jason and Carter's original R code
- **src:** features.py, validation.py, utils.py
- *bootstrap.py* - Script to boot up local dev/production environment, install requirements inside virtualenv, set up AWS permissions, etc.
- *fabfile.py* - A collection of reusable fab functions for deploying things to AWS.
- *model_generator.py* - Finalized production model code that we can run on AWS.
- *predicting_the_next_pitch.ipynb* - Where we do most of the work, getting our hands dirty, doing the initial model building, etc.
- *README.md* - Readme file
- *requirements.txt* - Packages and dependencies
