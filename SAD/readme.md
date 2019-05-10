# Objectives

An equilibrium database would make it quick and easy for users to look at the thermal profiles of the spacecraft subsystems(with emphasis on HRMA, OBA + SIM) at given positions. Looking at these profiles users should understand how pitch, duration and other positional factors affect temperature of components. 
The smart anomaly detection will use past thermal profiles to build models and with every new telemetry pass answer the question: does something not make sense. If it finds that there are thermal anomalies then the user should be notified and given a sense of where things went wrong. 

## Click [latest_models](https://github.com/chandra-mta/mtanb/blob/master/SAD/latest_models/readme.md) to see the most up-to-date best models for our test MSIDs
Notes on the May 9th updates: 
Using methods described by [Gal(2016)](http://papers.nips.cc/paper/6241-a-theoretically-grounded-application-of-dropout-in-recurrent-neural-networks.pdf) and [Zhu(2017)](https://arxiv.org/abs/1709.01907) I've added uncertainty to the LSTM neural network - this uncertainty theoretically accounts for model uncertainty, model misspecification and inherent noise. I've found that uncertainties remain pretty constant throughout - which may be a bug. Next and the most important step is to truly test anomaly detection.

## Current next steps (in order of importance) (updated May 10 2019)
- Test anomaly detection with this
- Expanding list of msids we build models with 
- Looking into using genetic algorithms for feature selection and other ways to do feature selection
- Visualization of learning
