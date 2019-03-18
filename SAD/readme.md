# Objectives

An equilibrium database would make it quick and easy for users to look at the thermal profiles of the spacecraft subsystems(with emphasis on HRMA, OBA + SIM) at given positions. Looking at these profiles users should understand how pitch, duration and other positional factors affect temperature of components. 
The smart anomaly detection will use past thermal profiles to build models and with every new telemetry pass answer the question: does something not make sense. If it finds that there are thermal anomalies then the user should be notified and given a sense of where things went wrong. 

##Look at latest_models to see the most up-to-date best models for our test MSIDs

##Current next steps (in order of importance) 
- Attach errors to each prediction, test anomaly detection with this
- Expanding list of msids we build models with 
- Looking into using genetic algorithms for feature selection and other ways to do feature selection
