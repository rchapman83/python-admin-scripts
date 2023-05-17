# ntp-script

# detectify-script
Before running this script OS Environmental Variavles DETFY_KEY and DETFY_SECRET_KEY must be present.

DETFY_KEY = Detectify API-key
DETFY_SECRET_KEY = Detectify API-secret

# cleanup-script
:snake: A pair of Python 3+ scripts i've put together to clean up those pesky log directories.

**cleanup_basic** is a simple script using only Python core modules for simple deployment.

**cleanup_extended** makes use of additional modules and has more complex logging.<br>
I'll probably add some additional features in the future, perhaps compressing and archiving of logs.

## Usage
`python cleanup_basic.py <number of days old> <directory path>` <br>
`python cleanup_extended.py <number of days old> <directory path>` 
