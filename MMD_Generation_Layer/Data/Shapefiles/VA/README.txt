Virginia 2024 General Election Precinct-Level Results and Boundaries

## RDH Date Retrieval
03/16/26

## Sources
Election results from Virginia Department of Elections Historic Elections Database (https://historical.elections.virginia.gov/)

Rockingham County results come from the state's elections viewer (https://enr.elections.virginia.gov/results/public/Virginia/elections/2024NovemberGeneral) and are modified to remove the double counting of absentee votes that was incorrectly certified by the state.

Precinct boundaries from Virginia Department of Elections (https://www.elections.virginia.gov/casting-a-ballot/redistricting/interactive-map/). 

Emporia City precincts edited using online precinct description and precincts in Covington City and Northampton County were aligned to online precinct maps.

The precinct boundaries were all checked against the L2 voter file closest to the November 2024 general election. The date of this voter file is February 13, 2025.

## Notes on Field Names:
Columns reporting votes generally follow the pattern:
One example is:
GPREDCLI
The first character is G for a general election, P for a primary, S for a special, and R for a runoff.
Characters 2 and 3 are the year of the election.
Characters 4-6 represent the office type (see list below).
Character 7 represents the party of the candidate.
Characters 8-10 are the first three letters of the candidate's last name.

Office Codes Used:
PRE - President of the United States
CON## - U.S. Congress
USS - United States Senate

Party Codes Used:
D - Democratic
G - Green
I - Independent
L - Libertarian
O - Other
R - Republican


## Fields:
Field Name  Description                                                                    
UNIQUE_ID   Unique ID for each precinct                                                    
COUNTYFP    County FIP identifier                                                          
Cnty/City   County or City Name                                                             
Pct         Precinct
CONG_DIST   Congressional District
G24PREDHAR  Kamala D. Harris, Democratic, President General Election                       
G24PREGSTE  Jill E. Stein, Green, President General Election                               
G24PREICRU  Claudia De La Cruz, Independent, President General Election                    
G24PREIWES  Cornel R. West, Independent, President General Election                        
G24PRELOLI  Chase R. Oliver, Libertarian, President General Election                       
G24PREOOTH  All Others, Other, President General Election                                  
G24PRERTRU  Donald J. Trump, Republican, President General Election                        
G24USSDKAI  Timothy M. Kaine, Democratic, U S Senate General Election                      
G24USSOOTH  All Others, Other, U S Senate General Election                                 
G24USSRCAO  Hung Cao, Republican, U S Senate General Election                              
GCON01DMEH  Leslie C. Mehta, Democratic, U S House General Election District 1             
GCON01OOTH  All Others, Other, U S House General Election District 1                       
GCON01RWIT  Robert J. Wittman, Republican, U S House General Election District 1           
GCON02DSMA  Missy Cotter Smasal, Democratic, U S House General Election District 2         
GCON02IREI  Robert E. Reid, Jr, Independent, U S House General Election District 2         
GCON02OOTH  All Others, Other, U S House General Election District 2                       
GCON02RKIG  Jen A. Kiggans, Republican, U S House General Election District 2              
GCON03DSCO  Robert C. "Bobby" Scott, Democratic, U S House General Election District 3     
GCON03OOTH  All Others, Other, U S House General Election District 3                       
GCON03RSIT  John Sitka, III, Republican, U S House General Election District 3             
GCON04DMCC  Jennifer L. McClellan, Democratic, U S House General Election District 4       
GCON04OOTH  All Others, Other, U S House General Election District 4                       
GCON04RMOH  William J. "Bill" Moher, III, Republican, U S House General Election District 4
GCON05DWIT  Gloria Tinsley Witt, Democratic, U S House General Election District 5         
GCON05OOTH  All Others, Other, U S House General Election District 5                       
GCON05RMCG  John J. McGuire, III, Republican, U S House General Election District 5        
GCON06DMIT  Ken L. Mitchell, Democratic, U S House General Election District 6             
GCON06IWEL  Robert C. "Robby" Wells, Jr, Independent, U S House General Election District 6
GCON06OOTH  All Others, Other, U S House General Election District 6                       
GCON06RCLI  Ben L. Cline, Republican, U S House General Election District 6                
GCON07DVIN  Eugene S. Vindman, Democratic, U S House General Election District 7           
GCON07OOTH  All Others, Other, U S House General Election District 7                       
GCON07RAND  Derrick M. Anderson, Republican, U S House General Election District 7         
GCON08DBEY  Donald S. Beyer, Jr, Democratic, U S House General Election District 8         
GCON08IHEN  Bentley F. Hensel, Independent, U S House General Election District 8          
GCON08IKEN  David R. Kennedy, Independent, U S House General Election District 8           
GCON08OOTH  All Others, Other, U S House General Election District 8                       
GCON08RTOR  Jerry W. Torres, Republican, U S House General Election District 8             
GCON09DBAK  Karen H. G. Baker, Democratic, U S House General Election District 9           
GCON09OOTH  All Others, Other, U S House General Election District 9                       
GCON09RGRI  H. Morgan Griffith, Republican, U S House General Election District 9          
GCON10DSUB  Suhas Subramanyam, Democratic, U S House General Election District 10          
GCON10OOTH  All Others, Other, U S House General Election District 10                      
GCON10RCLA  Mike W. Clancy, Republican, U S House General Election District 10             
GCON11DCON  Gerald E. "Gerry" Connolly, Democratic, U S House General Election District 11 
GCON11OOTH  All Others, Other, U S House General Election District 11                      
GCON11RMET  Mike L. Van Meter, Republican, U S House General Election District 11          
                                                                    

## Processing Steps
In the precinct-level results, some precincts appear multiple times, with either "State District" or "City District" included after the name, these sub-precinct units have been dissolved in order to match precinct boundaries. Citywide and countywide absentee and provisional ballots were allocated to precincts based on each precincts' share of precinct-level votes for a particular candidate within the relevant geography. 

After joining the precincts to their boundaries, the files were checked for precinct-district splits. Ultimately, the precinct boundary and election result files are split across two files. The "_all_" file contains all the election results joined to precinct boundaries, but does not account for the various precinct-district splits identified in processing and as such, does not contain district assignments. The "_cong_" file contains Congressional results at the most granular units for which data is available. The "Bedford County-:-104 - Barnhardt Baptist Church" precinct contains 6 total votes for Congressional District 6 candidates (GCON06DMIT:4, GCON06RCLI:2) even though the county is outside of this district, these votes are removed from the "_cong_" file. Please note that in order to minimize superfluous splits, precinct splits are only made when a precinct contains votes for candidates in multiple districts, as such district assignments for precincts many not perfectly correspond to the districts themselves, particularly in large, uninhabited areas.

In a few precincts across the state, minor differences were observed between the state's provided precinct boundaries and those suggested by the L2 voter file. We are in the process of clarifying these discrepancies with the counties and if needed, this file will be updated and downloaders of the file notified. 

Election results were aggregated to the state-level and compared against official election results from the state (https://enr.elections.virginia.gov/results/public/Virginia/elections/2024NovemberGeneral). Totals matched in all instances except Rockingham County, which was incorrectly certified by the state. Rockingham County values match those from the county's votes abstract (https://www.rockinghamcountyva.gov/DocumentCenter/View/21060/Final-Abstracts-Nov-5-2024).

Please direct questions related to processing this dataset to info@redistrictingdatahub.org.
