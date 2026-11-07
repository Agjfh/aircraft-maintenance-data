Data Set: FD001
Train trajectories: 100
Test trajectories: 100
Conditions: ONE (Sea Level)
Fault Modes: ONE (HPC Degradation)

Data Set: FD002
Train trajectories: 260
Test trajectories: 259
Conditions: SIX
Fault Modes: ONE (HPC Degradation)

Data Set: FD003
Train trajectories: 100
Test trajectories: 100
Conditions: ONE (Sea Level)
Fault Modes: TWO (HPC Degradation, Fan Degradation)

Data Set: FD004
Train trajectories: 248
Test trajectories: 249
Conditions: SIX
Fault Modes: TWO (HPC Degradation, Fan Degradation)

Experimental Scenario

The data sets consist of multiple multivariate time series. Each data set is divided into training and test subsets. Each time series is from a different engine; data can be considered to be from a fleet of engines of the same type. Each engine starts with different degrees of initial wear and manufacturing variation which is unknown to the user. This wear and variation is considered normal, not a fault condition. Three operational settings substantially affect engine performance. The data are contaminated with sensor noise.

The engine operates normally at the start of each time series and develops a fault at some point. In the training set, the fault grows until system failure. In the test set, the time series ends before failure. The objective is to predict the number of remaining operating cycles before failure for each test engine. True Remaining Useful Life (RUL) values are also provided for the test data.

The original data are zip-compressed text files with 26 numeric columns separated by spaces: unit number, cycle, three operational settings, and 21 sensor measurements.

Reference: A. Saxena, K. Goebel, D. Simon, and N. Eklund, “Damage Propagation Modeling for Aircraft Engine Run-to-Failure Simulation,” Proceedings of the International Conference on Prognostics and Health Management (PHM08), Denver, CO, October 2008.
