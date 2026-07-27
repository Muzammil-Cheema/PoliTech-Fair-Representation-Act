South Carolina 2024 General Election Precinct-Level Results and Boundaries

## RDH Date Retrieval
12/20/2024

## Sources
The RDH retrieved 2024 general election precinct-level results from the South Carolina Secretary of State [website] (https://www.enr-scvotes.org/SC/122436/web.345435/#/summary). The RDH navigated to each county's election results page and clicked "Detail XML", to get the results at the precinct level.

Shapefiles via [South Carolina Revenue and Fiscal Affairs Office](https://rfa.sc.gov/programs-services/precinct-demographics/jurisdictional-mapping/political-gis-data)

## Notes on Field Names:
Columns reporting votes generally follow the pattern: 
One example is:
G16PREDCLI
The first character is G for a general election, P for a primary, S for a special, and R for a runoff.
Characters 2 and 3 are the year of the election.*
Characters 4-6 represent the office type (see list below).
Character 7 represents the party of the candidate.
Characters 8-10 are the first three letters of the candidate's last name.

*To fit within the GIS 10 character limit for field names, the naming convention is slightly different for the State Legislature and US House of Representatives. All fields are listed below with definitions.

Office Codes Used:
PRE - United States President
CON## - U.S. Congress
SL###  - State Legislative Lower
SU##  - State Legislative Upper


A - Alliance
C - Constitution Party
D - Democratic
G - Green
I - Independent
L - Libertarian Party
O - Other / Write In
R - Republican
U - United Citizens Party
W - Workers Party

## Fields:
Field Name Description 
UNIQUE_ID  State FIP Value
COUNTY_NAM County Name                                        
COUNTYFP   County FIP Value                                       
CDE_COUNTY County Code                                            
PCTNUM     Precinct Number 
PCTNAME    Precinct Name 

***sc_2024_gen_st_prec*** 
G24PRECTER	President and Vice President	CON Randall A Terry/Stephen E Broden
G24PREDHAR	President and Vice President	DEM Kamala D Harris/Tim Walz
G24PREGSTE	President and Vice President	GRN Jill Stein/Rudolph Butch Ware
G24PRELCHA	President and Vice President	LIB Chase Oliver/Mike ter Maat
G24PRERTRU	President and Vice President	REP Donald J Trump/JD Vance
G24PREUWES	President and Vice President	UNC Cornel West/Melina Abdulla
G24PREWCRU	President and Vice President	WRK Claudia De La Cruz/Karina Garcia

***sc_2024_gen_cong_prec***
CONG_DIST  South Carolina Congressional District   
GCON01DMOO	U.S.  House of Representatives, District  1	DEM Michael B Moore
GCON01OWRI	U.S.  House of Representatives, District  1	OTHER Write-In
GCON01RMAC	U.S.  House of Representatives, District  1	REP Nancy Mace
GCON02DROB	U.S.  House of Representatives, District  2	DEM David Robinson II
GCON02OWRI	U.S.  House of Representatives, District  2	OTHER Write-In
GCON02RWIL	U.S.  House of Representatives, District  2	REP Joe Wilson
GCON03ABED	U.S.  House of Representatives, District  3	ALN Mike Bedenbaugh
GCON03DBES	U.S.  House of Representatives, District  3	DEM Bryon L Best
GCON03OWRI	U.S.  House of Representatives, District  3	OTHER Write-In
GCON03RBIG	U.S.  House of Representatives, District  3	REP Sheri Biggs
GCON04CHAC	U.S.  House of Representatives, District  4	CON Mark Hackett
GCON04DHAR	U.S.  House of Representatives, District  4	DEM Kathryn Harvey
GCON04OWRI	U.S.  House of Representatives, District  4	OTHER Write-In
GCON04RTIM	U.S.  House of Representatives, District  4	REP William Timmons
GCON05DHUN	U.S.  House of Representatives, District  5	DEM Evangeline Hundley
GCON05OWRI	U.S.  House of Representatives, District  5	OTHER Write-In
GCON05RNOR	U.S.  House of Representatives, District  5	REP Ralph W Norman
GCON06AODD	U.S.  House of Representatives, District  6	ALN Joseph Oddo
GCON06DCLY	U.S.  House of Representatives, District  6	DEM James E Jim Clyburn
GCON06LSIM	U.S.  House of Representatives, District  6	LIB Michael Simpson
GCON06OWRI	U.S.  House of Representatives, District  6	OTHER Write-In
GCON06RBUC	U.S.  House of Representatives, District  6	REP Duke Buckner
GCON06UDIX	U.S.  House of Representatives, District  6	UNC Gregg Marcel Dixon
GCON07DHYM	U.S.  House of Representatives, District  7	DEM Mal Hyman
GCON07OWRI	U.S.  House of Representatives, District  7	OTHER Write-In
GCON07RFRY	U.S.  House of Representatives, District  7	REP Russell Fry

***sc_2024_gen_sldu_prec***
SLDU_DIST  South Carolina Senate District  
GSU01OWRI	State  Senate, District  1	OTHER Write-In
GSU01RALE	State  Senate, District  1	REP Thomas C Alexander
GSU02OWRI	State  Senate, District  2	OTHER Write-In
GSU02RRIC	State  Senate, District  2	REP Rex F Rice
GSU03DSPE	State  Senate, District  3	DEM Jessicka Spearman
GSU03OWRI	State  Senate, District  3	OTHER Write-In
GSU03RCAS	State  Senate, District  3	REP Richard Cash
GSU04OWRI	State  Senate, District  4	OTHER Write-In
GSU04RGAM	State  Senate, District  4	REP Mike Gambrell
GSU05OWRI	State  Senate, District  5	OTHER Write-In
GSU05RCOR	State  Senate, District  5	REP Tom Corbin
GSU06OWRI	State  Senate, District  6	OTHER Write-In
GSU06RELL	State  Senate, District  6	REP Jason Elliott
GSU07DALL	State  Senate, District  7	DEM Karl B Allen
GSU07OWRI	State  Senate, District  7	OTHER Write-In
GSU08DCUL	State  Senate, District  8	DEM Taylor Culliver
GSU08OWRI	State  Senate, District  8	OTHER Write-In
GSU08RTUR	State  Senate, District  8	REP Ross Turner
GSU09DDRI	State  Senate, District  9	DEM C Randy Driggers
GSU09OWRI	State  Senate, District  9	OTHER Write-In
GSU09RVER	State  Senate, District  9	REP Danny Verdin
GSU10DKLE	State  Senate, District  10	DEM Francie Kleckley
GSU10OWRI	State  Senate, District  10	OTHER Write-In
GSU10RGAR	State  Senate, District  10	REP Billy Garrett
GSU11DGET	State  Senate, District  11	DEM Angela L Geter
GSU11OWRI	State  Senate, District  11	OTHER Write-In
GSU11RKIM	State  Senate, District  11	REP Josh Kimbrell
GSU12DAMA	State  Senate, District  12	DEM Octavia Amaechi
GSU12OWRI	State  Senate, District  12	OTHER Write-In
GSU12RNUT	State  Senate, District  12	REP Roger Allen Nutt
GSU13OWRI	State  Senate, District  13	OTHER Write-In
GSU13RMAR	State  Senate, District  13	REP Shane Martin
GSU14OWRI	State  Senate, District  14	OTHER Write-In
GSU14RPEE	State  Senate, District  14	REP Harvey Peeler
GSU15AWOR	State  Senate, District  15	ALN Sarah Work
GSU15OWRI	State  Senate, District  15	OTHER Write-In
GSU15RCLI	State  Senate, District  15	REP Wes Climer
GSU16OWRI	State  Senate, District  16	OTHER Write-In
GSU16RJOH	State  Senate, District  16	REP Michael Johnson
GSU16WMAC	State  Senate, District  16	WRK Kiral Mace
GSU17DFAN	State  Senate, District  17	DEM Mike Fanning
GSU17OWRI	State  Senate, District  17	OTHER Write-In
GSU17RSTU	State  Senate, District  17	REP Everett Stubbs
GSU18OWRI	State  Senate, District  18	OTHER Write-In
GSU18RCRO	State  Senate, District  18	REP Ronnie Cromer
GSU19DDEV	State  Senate, District  19	DEM Tameika Isaac Devine
GSU19OWRI	State  Senate, District  19	OTHER Write-In
GSU19UNEL	State  Senate, District  19	UNC Chris Nelums
GSU20DSUT	State  Senate, District  20	DEM Ed Sutton
GSU20LLUD	State  Senate, District  20	LIB Kendal Ludden
GSU20OWRI	State  Senate, District  20	OTHER Write-In
GSU21DJAC	State  Senate, District  21	DEM Darrell Jackson
GSU21OWRI	State  Senate, District  21	OTHER Write-In
GSU22DWAL	State  Senate, District  22	DEM Overture Walker
GSU22OWRI	State  Senate, District  22	OTHER Write-In
GSU23OWRI	State  Senate, District  23	OTHER Write-In
GSU23RKEN	State  Senate, District  23	REP Carlisle Kennedy
GSU24DELD	State  Senate, District  24	DEM Dee Elder
GSU24OWRI	State  Senate, District  24	OTHER Write-In
GSU24RYOU	State  Senate, District  24	REP Tom Young
GSU25OWRI	State  Senate, District  25	OTHER Write-In
GSU25RMAS	State  Senate, District  25	REP Shane Massey
GSU26DOTT	State  Senate, District  26	DEM Russell Ott
GSU26OWRI	State  Senate, District  26	OTHER Write-In
GSU26RGUE	State  Senate, District  26	REP Jason Guerry
GSU27DCUR	State  Senate, District  27	DEM Yokima Cureton
GSU27OWRI	State  Senate, District  27	OTHER Write-In
GSU27RBLA	State  Senate, District  27	REP Allen Blackmon
GSU28OWRI	State  Senate, District  28	OTHER Write-In
GSU28RHEM	State  Senate, District  28	REP Greg Hembree
GSU29DMAL	State  Senate, District  29	DEM Gerald Malloy
GSU29OWRI	State  Senate, District  29	OTHER Write-In
GSU29RCHA	State  Senate, District  29	REP JD Chaplin
GSU30DWIL	State  Senate, District  30	DEM Kent M Williams
GSU30OWRI	State  Senate, District  30	OTHER Write-In
GSU30RBER	State  Senate, District  30	REP Rodney Berry
GSU31DTIM	State  Senate, District  31	DEM Belinda Timmons
GSU31OWRI	State  Senate, District  31	OTHER Write-In
GSU31RREI	State  Senate, District  31	REP Mike Reichenbach
GSU32DSAB	State  Senate, District  32	DEM Ronnie A Sabb
GSU32OWRI	State  Senate, District  32	OTHER Write-In
GSU33DBEM	State  Senate, District  33	DEM Pete John Bember
GSU33OWRI	State  Senate, District  33	OTHER Write-In
GSU33RRAN	State  Senate, District  33	REP Luke A Rankin
GSU34OWRI	State  Senate, District  34	OTHER Write-In
GSU34RGOL	State  Senate, District  34	REP Stephen Goldfinch
GSU35DGRA	State  Senate, District  35	DEM Jeffrey R Graham
GSU35OWRI	State  Senate, District  35	OTHER Write-In
GSU35RJON	State  Senate, District  35	REP Mike Jones
GSU36DJOH	State  Senate, District  36	DEM Kevin L Johnson
GSU36OWRI	State  Senate, District  36	OTHER Write-In
GSU36RZEL	State  Senate, District  36	REP Jeff Zell
GSU37OWRI	State  Senate, District  37	OTHER Write-In
GSU37RGRO	State  Senate, District  37	REP Larry Grooms
GSU38OWRI	State  Senate, District  38	OTHER Write-In
GSU38RBEN	State  Senate, District  38	REP Sean Bennett
GSU39DSTE	State  Senate, District  39	DEM Vernon Stephens
GSU39OWRI	State  Senate, District  39	OTHER Write-In
GSU39RFER	State  Senate, District  39	REP Tom Fernandez
GSU40DHUT	State  Senate, District  40	DEM Brad Hutto
GSU40OWRI	State  Senate, District  40	OTHER Write-In
GSU40RCAR	State  Senate, District  40	REP Sharon Carter
GSU41DADK	State  Senate, District  41	DEM Rita Adkins
GSU41OWRI	State  Senate, District  41	OTHER Write-In
GSU41RLEB	State  Senate, District  41	REP Matt Leber
GSU42DTED	State  Senate, District  42	DEM Deon Tedder
GSU42OWRI	State  Senate, District  42	OTHER Write-In
GSU43DHUS	State  Senate, District  43	DEM Julie Cofer Hussey
GSU43OWRI	State  Senate, District  43	OTHER Write-In
GSU43RCAM	State  Senate, District  43	REP Chip Campsen
GSU44DWYN	State  Senate, District  44	DEM Vicky Wynn
GSU44OWRI	State  Senate, District  44	OTHER Write-In
GSU44RADA	State  Senate, District  44	REP Brian Adams
GSU45DMAT	State  Senate, District  45	DEM Margie Bright Matthews
GSU45OWRI	State  Senate, District  45	OTHER Write-In
GSU46DSAU	State  Senate, District  46	DEM Gwyneth J Saunders
GSU46OWRI	State  Senate, District  46	OTHER Write-In
GSU46RDAV	State  Senate, District  46	REP Tom Davis

***sc_2024_gen_sldl_prec***
SLDL_DIST  South Carolina House of Representatives District
GSL001OWRI	State  House of Representatives, District  1	OTHER Write-In
GSL001RWHI	State  House of Representatives, District  1	REP Bill Whitmire
GSL002OWRI	State  House of Representatives, District  2	OTHER Write-In
GSL002RDUN	State  House of Representatives, District  2	REP Adam Duncan
GSL003DLEH	State  House of Representatives, District  3	DEM Eunice Lehmacher
GSL003OWRI	State  House of Representatives, District  3	OTHER Write-In
GSL003RBOW	State  House of Representatives, District  3	REP Phillip Bowers
GSL004OWRI	State  House of Representatives, District  4	OTHER Write-In
GSL004RHIO	State  House of Representatives, District  4	REP Davey Hiott
GSL005OWRI	State  House of Representatives, District  5	OTHER Write-In
GSL005RCOL	State  House of Representatives, District  5	REP Neal Collins
GSL006DWAG	State  House of Representatives, District  6	DEM Tony Wagoner
GSL006OWRI	State  House of Representatives, District  6	OTHER Write-In
GSL006RCRO	State  House of Representatives, District  6	REP April Cromer
GSL007LSAV	State  House of Representatives, District  7	LIB Hunter Savirino
GSL007OWRI	State  House of Representatives, District  7	OTHER Write-In
GSL007RGIL	State  House of Representatives, District  7	REP Lee Gilreath
GSL008ATOD	State  House of Representatives, District  8	ALN Jackie Todd
GSL008OWRI	State  House of Representatives, District  8	OTHER Write-In
GSL008RCHA	State  House of Representatives, District  8	REP Don Chapman
GSL009OWRI	State  House of Representatives, District  9	OTHER Write-In
GSL009RSAN	State  House of Representatives, District  9	REP Blake Sanders
GSL010OWRI	State  House of Representatives, District  10	OTHER Write-In
GSL010RBEA	State  House of Representatives, District  10	REP Thomas Beach
GSL011OWRI	State  House of Representatives, District  11	OTHER Write-In
GSL011RGAG	State  House of Representatives, District  11	REP Craig Gagnon
GSL012DBRO	State  House of Representatives, District  12	DEM Jumelle Brooks
GSL012OWRI	State  House of Representatives, District  12	OTHER Write-In
GSL012RGIB	State  House of Representatives, District  12	REP Daniel Gibson
GSL013DKIM	State  House of Representatives, District  13	DEM Bill Kimler
GSL013OWRI	State  House of Representatives, District  13	OTHER Write-In
GSL013RMCC	State  House of Representatives, District  13	REP John McCravy
GSL014OWRI	State  House of Representatives, District  14	OTHER Write-In
GSL014RRAN	State  House of Representatives, District  14	REP Luke Rankin
GSL015DMOO	State  House of Representatives, District  15	DEM JA Moore
GSL015OWRI	State  House of Representatives, District  15	OTHER Write-In
GSL015RWAL	State  House of Representatives, District  15	REP Carlton Walker
GSL016OWRI	State  House of Representatives, District  16	OTHER Write-In
GSL016RWIL	State  House of Representatives, District  16	REP Mark N Willis
GSL017OWRI	State  House of Representatives, District  17	OTHER Write-In
GSL017RBUR	State  House of Representatives, District  17	REP Mike Burns
GSL018OWRI	State  House of Representatives, District  18	OTHER Write-In
GSL018RMOR	State  House of Representatives, District  18	REP Alan Morgan
GSL019OWRI	State  House of Representatives, District  19	OTHER Write-In
GSL019RHAD	State  House of Representatives, District  19	REP Patrick Haddon
GSL020DDRE	State  House of Representatives, District  20	DEM Stephen Dreyfus
GSL020OWRI	State  House of Representatives, District  20	OTHER Write-In
GSL020RFRA	State  House of Representatives, District  20	REP Stephen Frank
GSL021OWRI	State  House of Representatives, District  21	OTHER Write-In
GSL021RCOX	State  House of Representatives, District  21	REP Bobby J Cox
GSL022DFOW	State  House of Representatives, District  22	DEM Brann Fowler
GSL022OWRI	State  House of Representatives, District  22	OTHER Write-In
GSL022RWIC	State  House of Representatives, District  22	REP Paul Wickensimer
GSL023DDIL	State  House of Representatives, District  23	DEM Chandra Dillard
GSL023LATK	State  House of Representatives, District  23	LIB James Archibald Atkins Jr
GSL023OWRI	State  House of Representatives, District  23	OTHER Write-In
GSL024DJOH	State  House of Representatives, District  24	DEM Shauna R Johnson
GSL024OWRI	State  House of Representatives, District  24	OTHER Write-In
GSL024RBAN	State  House of Representatives, District  24	REP Bruce Bannister
GSL025DJON	State  House of Representatives, District  25	DEM Wendell Jones
GSL025OWRI	State  House of Representatives, District  25	OTHER Write-In
GSL025RKEN	State  House of Representatives, District  25	REP Tim Kennedy
GSL026DVIL	State  House of Representatives, District  26	DEM Matt Vilardebo
GSL026OWRI	State  House of Representatives, District  26	OTHER Write-In
GSL026RMAR	State  House of Representatives, District  26	REP David Martin
GSL027DMAC	State  House of Representatives, District  27	DEM John MacCarthy
GSL027OWRI	State  House of Representatives, District  27	OTHER Write-In
GSL027RVAU	State  House of Representatives, District  27	REP David Vaughan
GSL028DWIE	State  House of Representatives, District  28	DEM J Fritz Wiebel
GSL028OWRI	State  House of Representatives, District  28	OTHER Write-In
GSL028RHUF	State  House of Representatives, District  28	REP Chris Huff
GSL029OWRI	State  House of Representatives, District  29	OTHER Write-In
GSL029RMOS	State  House of Representatives, District  29	REP Dennis Moss
GSL030DMCD	State  House of Representatives, District  30	DEM Ysante McDowell
GSL030OWRI	State  House of Representatives, District  30	OTHER Write-In
GSL030RLAW	State  House of Representatives, District  30	REP Brian Lawson
GSL031DHEN	State  House of Representatives, District  31	DEM Rosalyn Henderson-Myers
GSL031OWRI	State  House of Representatives, District  31	OTHER Write-In
GSL032OWRI	State  House of Representatives, District  32	OTHER Write-In
GSL032RMON	State  House of Representatives, District  32	REP Scott Montgomery
GSL033DTUR	State  House of Representatives, District  33	DEM Clemson Turregano
GSL033OWRI	State  House of Representatives, District  33	OTHER Write-In
GSL033RMOO	State  House of Representatives, District  33	REP Travis A Moore
GSL034OWRI	State  House of Representatives, District  34	OTHER Write-In
GSL034REDG	State  House of Representatives, District  34	REP Sarita Edgerton
GSL035OWRI	State House of Representatives, District 35	OTHER Write-In
GSL035RCHU	State House of Representatives, District 35	REP Bill Chumley
GSL036OWRI	State  House of Representatives, District  36	OTHER Write-In
GSL036RHAR	State  House of Representatives, District  36	REP Rob Harris
GSL037OWRI	State  House of Representatives, District  37	OTHER Write-In
GSL037RLON	State  House of Representatives, District  37	REP Steven Long
GSL038DTAY	State  House of Representatives, District  38	DEM JR Taylor
GSL038OWRI	State  House of Representatives, District  38	OTHER Write-In
GSL038RMAG	State  House of Representatives, District  38	REP Josiah Magnuson
GSL039OWRI	State  House of Representatives, District  39	OTHER Write-In
GSL039RFOR	State  House of Representatives, District  39	REP Cal Forrest
GSL040OWRI	State  House of Representatives, District  40	OTHER Write-In
GSL040RWHI	State  House of Representatives, District  40	REP Joe White
GSL041DMCD	State  House of Representatives, District  41	DEM Annie E McDaniel
GSL041OWRI	State  House of Representatives, District  41	OTHER Write-In
GSL042DGOS	State  House of Representatives, District  42	DEM David Gossett
GSL042OWRI	State  House of Representatives, District  42	OTHER Write-In
GSL042RGIL	State  House of Representatives, District  42	REP Doug Gilliam
GSL043OWRI	State  House of Representatives, District  43	OTHER Write-In
GSL043RLIG	State  House of Representatives, District  43	REP Randy Ligon
GSL044DCRO	State  House of Representatives, District  44	DEM Katie Crosby
GSL044OWRI	State  House of Representatives, District  44	OTHER Write-In
GSL044RNEE	State  House of Representatives, District  44	REP Mike Neese
GSL045DVEN	State  House of Representatives, District  45	DEM Nicole Ventour
GSL045OWRI	State  House of Representatives, District  45	OTHER Write-In
GSL045RNEW	State  House of Representatives, District  45	REP Brandon Newton
GSL046DZAB	State  House of Representatives, District  46	DEM John Zabel
GSL046OWRI	State  House of Representatives, District  46	OTHER Write-In
GSL046RSES	State  House of Representatives, District  46	REP Heath Sessions
GSL047OWRI	State  House of Representatives, District  47	OTHER Write-In
GSL047RPOP	State  House of Representatives, District  47	REP Tommy Pope
GSL048OWRI	State  House of Representatives, District  48	OTHER Write-In
GSL048RGUF	State  House of Representatives, District  48	REP Brandon Guffey
GSL049DKIN	State  House of Representatives, District  49	DEM John R King
GSL049OWRI	State  House of Representatives, District  49	OTHER Write-In
GSL050DWHE	State  House of Representatives, District  50	DEM Will Wheeler
GSL050OWRI	State  House of Representatives, District  50	OTHER Write-In
GSL051DWEE	State  House of Representatives, District  51	DEM David Weeks
GSL051OWRI	State  House of Representatives, District  51	OTHER Write-In
GSL052DJOH	State  House of Representatives, District  52	DEM Jermaine Johnson
GSL052OWRI	State  House of Representatives, District  52	OTHER Write-In
GSL053DWAL	State  House of Representatives, District  53	DEM Bruce Wallace
GSL053OWRI	State  House of Representatives, District  53	OTHER Write-In
GSL053RYOW	State  House of Representatives, District  53	REP Richard Richie Yow
GSL054DLUC	State  House of Representatives, District  54	DEM Jason Scott Luck
GSL054OWRI	State  House of Representatives, District  54	OTHER Write-In
GSL054RMCD	State  House of Representatives, District  54	REP Sterling McDiarmid
GSL055DHAY	State  House of Representatives, District  55	DEM Jackie E Hayes
GSL055OWRI	State  House of Representatives, District  55	OTHER Write-In
GSL056OWRI	State  House of Representatives, District  56	OTHER Write-In
GSL056RMCG	State  House of Representatives, District  56	REP Tim McGinnis
GSL057DATK	State  House of Representatives, District  57	DEM Lucas Atkinson
GSL057OWRI	State  House of Representatives, District  57	OTHER Write-In
GSL057RCOL	State  House of Representatives, District  57	REP Kevin Taylor Coleridge
GSL058OWRI	State  House of Representatives, District  58	OTHER Write-In
GSL058RJOH	State  House of Representatives, District  58	REP Jeff Johnson
GSL059DALE	State  House of Representatives, District  59	DEM Terry Alexander
GSL059OWRI	State  House of Representatives, District  59	OTHER Write-In
GSL060OWRI	State  House of Representatives, District  60	OTHER Write-In
GSL060RLOW	State  House of Representatives, District  60	REP Phillip Lowe
GSL061OWRI	State  House of Representatives, District  61	OTHER Write-In
GSL061RSCH	State  House of Representatives, District  61	REP Carla Schuessler
GSL062DWIL	State  House of Representatives, District  62	DEM Robert Williams
GSL062OWRI	State  House of Representatives, District  62	OTHER Write-In
GSL063DHAS	State  House of Representatives, District  63	DEM Kory Haskins
GSL063OWRI	State  House of Representatives, District  63	OTHER Write-In
GSL063RJOR	State  House of Representatives, District  63	REP Jay Jordan
GSL064DBEL	State  House of Representatives, District  64	DEM Quadri Bell
GSL064OWRI	State  House of Representatives, District  64	OTHER Write-In
GSL064RPED	State  House of Representatives, District  64	REP Fawn Pedalino
GSL065OWRI	State  House of Representatives, District  65	OTHER Write-In
GSL065RMIT	State  House of Representatives, District  65	REP Cody T Mitchell
GSL066OWRI	State  House of Representatives, District  66	OTHER Write-In
GSL066RTER	State  House of Representatives, District  66	REP Jackie Terribile
GSL067OWRI	State  House of Representatives, District  67	OTHER Write-In
GSL067RSMI	State  House of Representatives, District  67	REP Murrell Smith
GSL068OWRI	State  House of Representatives, District  68	OTHER Write-In
GSL068RCRA	State  House of Representatives, District  68	REP Heather Ammons Crawford
GSL069LBRO	State  House of Representatives, District  69	LIB Allen James Broadus
GSL069OWRI	State  House of Representatives, District  69	OTHER Write-In
GSL069RWOO	State  House of Representatives, District  69	REP Chris Wooten
GSL070DREE	State  House of Representatives, District  70	DEM Robert Reese
GSL070OWRI	State  House of Representatives, District  70	OTHER Write-In
GSL071OWRI	State  House of Representatives, District  71	OTHER Write-In
GSL071RBAL	State  House of Representatives, District  71	REP Nathan Ballentine
GSL072DROS	State  House of Representatives, District  72	DEM Seth Rose
GSL072OWRI	State  House of Representatives, District  72	OTHER Write-In
GSL073DHAR	State  House of Representatives, District  73	DEM Chris Hart
GSL073OWRI	State  House of Representatives, District  73	OTHER Write-In
GSL074DRUT	State  House of Representatives, District  74	DEM Todd Rutherford
GSL074OWRI	State  House of Representatives, District  74	OTHER Write-In
GSL075DBAU	State  House of Representatives, District  75	DEM Heather Bauer
GSL075OWRI	State  House of Representatives, District  75	OTHER Write-In
GSL075RFIN	State  House of Representatives, District  75	REP Kirkman Finlay
GSL076DHOW	State  House of Representatives, District  76	DEM Leon Howard
GSL076OWRI	State  House of Representatives, District  76	OTHER Write-In
GSL076WVOT	State  House of Representatives, District  76	WRK Gary Votour
GSL077DGAR	State  House of Representatives, District  77	DEM Kambrell Garvin
GSL077OWRI	State  House of Representatives, District  77	OTHER Write-In
GSL078DBER	State  House of Representatives, District  78	DEM Beth Bernstein
GSL078OWRI	State  House of Representatives, District  78	OTHER Write-In
GSL079DGRA	State  House of Representatives, District  79	DEM Hamilton Grant
GSL079OWRI	State  House of Representatives, District  79	OTHER Write-In
GSL079RMAD	State  House of Representatives, District  79	REP Rebecca Madsen
GSL080DNEW	State  House of Representatives, District  80	DEM Donna Brown Newton
GSL080OWRI	State  House of Representatives, District  80	OTHER Write-In
GSL080RLAN	State  House of Representatives, District  80	REP Kathy Landing
GSL081DJEN	State  House of Representatives, District  81	DEM Jensen Jennings
GSL081OWRI	State  House of Representatives, District  81	OTHER Write-In
GSL081RHAR	State  House of Representatives, District  81	REP Charles Hartz
GSL082DCLY	State  House of Representatives, District  82	DEM William Bill Clyburn
GSL082OWRI	State  House of Representatives, District  82	OTHER Write-In
GSL082RSPU	State  House of Representatives, District  82	REP Suzanne Suzy Spurgeon
GSL083OWRI	State  House of Representatives, District  83	OTHER Write-In
GSL083RHIX	State  House of Representatives, District  83	REP Bill Hixon
GSL084OWRI	State  House of Representatives, District  84	OTHER Write-In
GSL084RORE	State  House of Representatives, District  84	REP Melissa Oremus
GSL085OWRI	State  House of Representatives, District  85	OTHER Write-In
GSL085RKIL	State  House of Representatives, District  85	REP Jay Kilmartin
GSL086OWRI	State  House of Representatives, District  86	OTHER Write-In
GSL086RTAY	State  House of Representatives, District  86	REP Bill Taylor
GSL087LMAC	State  House of Representatives, District  87	LIB Robin Machajewski
GSL087OWRI	State  House of Representatives, District  87	OTHER Write-In
GSL087RCAL	State  House of Representatives, District  87	REP Paula Rawl Calhoon
GSL088OWRI	State  House of Representatives, District  88	OTHER Write-In
GSL088RMAY	State  House of Representatives, District  88	REP RJ May
GSL089DBOR	State  House of Representatives, District  89	DEM Wayne Borders
GSL089OWRI	State  House of Representatives, District  89	OTHER Write-In
GSL089RCAS	State  House of Representatives, District  89	REP Micah Caskey
GSL090DBAM	State  House of Representatives, District  90	DEM Justin Bamberg
GSL090OWRI	State  House of Representatives, District  90	OTHER Write-In
GSL090RDIC	State  House of Representatives, District  90	REP H Frank Dickson
GSL091DHOS	State  House of Representatives, District  91	DEM Lonnie Hosey
GSL091OWRI	State  House of Representatives, District  91	OTHER Write-In
GSL091RKIN	State  House of Representatives, District  91	REP Ben Kinlaw
GSL092OWRI	State  House of Representatives, District  92	OTHER Write-In
GSL092RCOX	State  House of Representatives, District  92	REP Brandon Cox
GSL093DGOV	State  House of Representatives, District  93	DEM Jerry Govan
GSL093OWRI	State  House of Representatives, District  93	OTHER Write-In
GSL093RHAS	State  House of Representatives, District  93	REP Krista Hassell
GSL093WGED	State  House of Representatives, District  93	WRK Harold Geddings
GSL094OWRI	State  House of Representatives, District  94	OTHER Write-In
GSL094RGAT	State  House of Representatives, District  94	REP Gil Gatch
GSL095DCOB	State  House of Representatives, District  95	DEM Gilda Cobb-Hunter
GSL095OWRI	State  House of Representatives, District  95	OTHER Write-In
GSL096OWRI	State  House of Representatives, District  96	OTHER Write-In
GSL096RMCC	State  House of Representatives, District  96	REP D Ryan McCabe
GSL097OWRI	State  House of Representatives, District  97	OTHER Write-In
GSL097RROB	State  House of Representatives, District  97	REP Robby Robbins
GSL098DSAT	State  House of Representatives, District  98	DEM Sonja Ogletree Satani
GSL098OWRI	State  House of Representatives, District  98	OTHER Write-In
GSL098RMUR	State  House of Representatives, District  98	REP Chris Murphy
GSL099OWRI	State  House of Representatives, District  99	OTHER Write-In
GSL099RSMI	State  House of Representatives, District  99	REP Mark Smith
GSL100OWRI	State  House of Representatives, District  100	OTHER Write-In
GSL100RDAV	State  House of Representatives, District  100	REP Sylleste Davis
GSL101DKIR	State  House of Representatives, District  101	DEM Roger K Kirby
GSL101OWRI	State  House of Representatives, District  101	OTHER Write-In
GSL102DJEF	State  House of Representatives, District  102	DEM Joe Jefferson
GSL102OWRI	State  House of Representatives, District  102	OTHER Write-In
GSL102RHOL	State  House of Representatives, District  102	REP Harriet Holman
GSL103DAND	State  House of Representatives, District  103	DEM Carl L Anderson
GSL103OWRI	State  House of Representatives, District  103	OTHER Write-In
GSL104OWRI	State  House of Representatives, District  104	OTHER Write-In
GSL104RBAI	State  House of Representatives, District  104	REP William Bailey
GSL105OWRI	State  House of Representatives, District  105	OTHER Write-In
GSL105RHAR	State  House of Representatives, District  105	REP Kevin Hardee
GSL106OWRI	State  House of Representatives, District  106	OTHER Write-In
GSL106RGUE	State  House of Representatives, District  106	REP Val Guest
GSL107OWRI	State  House of Representatives, District  107	OTHER Write-In
GSL107RBRI	State  House of Representatives, District  107	REP Case Brittain
GSL108OWRI	State  House of Representatives, District  108	OTHER Write-In
GSL108RHEW	State  House of Representatives, District  108	REP Lee Hewitt
GSL109DSPA	State  House of Representatives, District  109	DEM Tiffany Spann-Wilder
GSL109OWRI	State  House of Representatives, District  109	OTHER Write-In
GSL110DMOF	State  House of Representatives, District  110	DEM John Moffett
GSL110OWRI	State  House of Representatives, District  110	OTHER Write-In
GSL110RHAR	State  House of Representatives, District  110	REP Tom Hartnett
GSL111DGIL	State  House of Representatives, District  111	DEM Wendell G Gilliard
GSL111LJER	State  House of Representatives, District  111	LIB Joe Jernigan
GSL111OWRI	State  House of Representatives, District  111	OTHER Write-In
GSL112DBRE	State  House of Representatives, District  112	DEM Peter Brennan
GSL112OWRI	State  House of Representatives, District  112	OTHER Write-In
GSL112RBUS	State  House of Representatives, District  112	REP Joe Bustos
GSL113DPEN	State  House of Representatives, District  113	DEM Marvin Rashad Pendarvis
GSL113OWRI	State  House of Representatives, District  113	OTHER Write-In
GSL114DLET	State  House of Representatives, District  114	DEM Adrienne Lett
GSL114OWRI	State  House of Representatives, District  114	OTHER Write-In
GSL114RBRE	State  House of Representatives, District  114	REP Gary Brewer
GSL115DWET	State  House of Representatives, District  115	DEM Spencer Wetmore
GSL115OWRI	State  House of Representatives, District  115	OTHER Write-In
GSL115RSLO	State  House of Representatives, District  115	REP J Warren Sloane
GSL116DMUR	State  House of Representatives, District  116	DEM Charlie Murray
GSL116OWRI	State  House of Representatives, District  116	OTHER Write-In
GSL116RTEE	State  House of Representatives, District  116	REP James Teeple
GSL117OWRI	State  House of Representatives, District  117	OTHER Write-In
GSL117RPAC	State  House of Representatives, District  117	REP Jordan Pace
GSL118DOWE	State  House of Representatives, District  118	DEM Charity Owens
GSL118OWRI	State  House of Representatives, District  118	OTHER Write-In
GSL118RHER	State  House of Representatives, District  118	REP Bill Herbkersman
GSL119DSTA	State  House of Representatives, District  119	DEM Leon Stavrinakis
GSL119OWRI	State  House of Representatives, District  119	OTHER Write-In
GSL119RMAG	State  House of Representatives, District  119	REP Brendan R Magee
GSL120DCRE	State  House of Representatives, District  120	DEM Kate Creech
GSL120OWRI	State  House of Representatives, District  120	OTHER Write-In
GSL120RNEW	State  House of Representatives, District  120	REP Weston Newton
GSL121DRIV	State  House of Representatives, District  121	DEM Michael F Rivers Sr
GSL121OWRI	State  House of Representatives, District  121	OTHER Write-In
GSL121RYUH	State  House of Representatives, District  121	REP Shelley Gay Yuhas
GSL122DWIL	State  House of Representatives, District  122	DEM Audrey Hopkins Williams
GSL122OWRI	State  House of Representatives, District  122	OTHER Write-In
GSL122RHAG	State  House of Representatives, District  122	REP Bill Hager
GSL123DCIF	State  House of Representatives, District  123	DEM Lisette Cifaldi
GSL123OWRI	State  House of Representatives, District  123	OTHER Write-In
GSL123RBRA	State  House of Representatives, District  123	REP Jeff Bradley
GSL124DHEN	State  House of Representatives, District  124	DEM Melinda Henrickson
GSL124OWRI	State  House of Representatives, District  124	OTHER Write-In
GSL124RERI	State  House of Representatives, District  124	REP Shannon Erickson

Some precincts are split across Congressional, House of Representatives or State Senate Districts. 

The shapefile provided by the state has invalid geometries, overlaps, gaps and holes in it. RDH used maup, a geospatial toolkit for redistricting data, as well as the state block file to fix the geometries.

There is also a "sc_2024_gen_prec_no_splits" file, which contains all election results, but does not include a SLDL_DIST, SLDU_DIST or CONG_DIST column.  

30 votes were recorded in Allendale County in the State Senate District 45 contest. No part of Allendale County is contained within District 45 and because we do not know the correct precinct for these votes they are dropped from sc_2024_gen_sldl_prec.

167 votes were recorded in Oakwood precinct in Richland County in the Congressional District 2 contest. No part of this precinct is contained within District 2 and because we do not know the correct precinct for these votes they are dropped from sc_2024_gen_cong_prec.

Please direct questions related to processing this dataset to info@redistrictingdatahub.org.  