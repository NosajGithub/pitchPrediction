copy player
from 's3://w210-pitch-prediction-test/gd_player.csv'
credentials 'aws_access_key_id=ASIAII4MFJ64ON27I6JQ;aws_secret_access_key=pKotUI7eodJIu1sjRitvMJwaO3qSM8opRo+WNOtm;token=AQoDYXdzEGgakAI6bAR5LX0fqLEhAgYqBR4V6O8HLP4Xar+P/swFy60y0P4lbriucIsrNdxNJP41TWc5U5VbEQ6gdkIP04jMk8/Ra0UkeneD1KqVw6ZWRP4jnPq/4MJjUHcWEA4mrDnDOV5AVOnpSLFFIGJhG91JDBNvgEU0EMHrt4puaB8ZCW2U1FoTTpl0m/arBtm61bFV/3UZUjIRwlYcKKVl8/YICd8b/LPmBhnb+uDNUhUORm15ljzqsSRr6BfYrtMXKLwQvBY8M3gawXOrnR9VnbSiy9QIY2T6iU2CB1305ZcBghni+ovnlbyiaTtA+ftzLMIix74PoOU3cmVCiJppuGPX0PC0rucThs0ADFf6ZqWMITEsSSCIuJKsBQ=='
removequotes
delimiter ','
null as 'NULL'
/* noload */
;

copy game
from 's3://w210-pitch-prediction-test/gd_game.csv'
credentials 'aws_access_key_id=ASIAII4MFJ64ON27I6JQ;aws_secret_access_key=pKotUI7eodJIu1sjRitvMJwaO3qSM8opRo+WNOtm;token=AQoDYXdzEGgakAI6bAR5LX0fqLEhAgYqBR4V6O8HLP4Xar+P/swFy60y0P4lbriucIsrNdxNJP41TWc5U5VbEQ6gdkIP04jMk8/Ra0UkeneD1KqVw6ZWRP4jnPq/4MJjUHcWEA4mrDnDOV5AVOnpSLFFIGJhG91JDBNvgEU0EMHrt4puaB8ZCW2U1FoTTpl0m/arBtm61bFV/3UZUjIRwlYcKKVl8/YICd8b/LPmBhnb+uDNUhUORm15ljzqsSRr6BfYrtMXKLwQvBY8M3gawXOrnR9VnbSiy9QIY2T6iU2CB1305ZcBghni+ovnlbyiaTtA+ftzLMIix74PoOU3cmVCiJppuGPX0PC0rucThs0ADFf6ZqWMITEsSSCIuJKsBQ=='
removequotes
delimiter ','
null as 'NULL'
/* noload */
;

copy hitchart
from 's3://w210-pitch-prediction-test/gd_hitchart.csv'
credentials 'aws_access_key_id=ASIAII4MFJ64ON27I6JQ;aws_secret_access_key=pKotUI7eodJIu1sjRitvMJwaO3qSM8opRo+WNOtm;token=AQoDYXdzEGgakAI6bAR5LX0fqLEhAgYqBR4V6O8HLP4Xar+P/swFy60y0P4lbriucIsrNdxNJP41TWc5U5VbEQ6gdkIP04jMk8/Ra0UkeneD1KqVw6ZWRP4jnPq/4MJjUHcWEA4mrDnDOV5AVOnpSLFFIGJhG91JDBNvgEU0EMHrt4puaB8ZCW2U1FoTTpl0m/arBtm61bFV/3UZUjIRwlYcKKVl8/YICd8b/LPmBhnb+uDNUhUORm15ljzqsSRr6BfYrtMXKLwQvBY8M3gawXOrnR9VnbSiy9QIY2T6iU2CB1305ZcBghni+ovnlbyiaTtA+ftzLMIix74PoOU3cmVCiJppuGPX0PC0rucThs0ADFf6ZqWMITEsSSCIuJKsBQ=='
removequotes
delimiter ','
null as 'NULL'
/* noload */
;

copy atbat
from 's3://w210-pitch-prediction-test/gd_atbat.csv'
credentials 'aws_access_key_id=ASIAII4MFJ64ON27I6JQ;aws_secret_access_key=pKotUI7eodJIu1sjRitvMJwaO3qSM8opRo+WNOtm;token=AQoDYXdzEGgakAI6bAR5LX0fqLEhAgYqBR4V6O8HLP4Xar+P/swFy60y0P4lbriucIsrNdxNJP41TWc5U5VbEQ6gdkIP04jMk8/Ra0UkeneD1KqVw6ZWRP4jnPq/4MJjUHcWEA4mrDnDOV5AVOnpSLFFIGJhG91JDBNvgEU0EMHrt4puaB8ZCW2U1FoTTpl0m/arBtm61bFV/3UZUjIRwlYcKKVl8/YICd8b/LPmBhnb+uDNUhUORm15ljzqsSRr6BfYrtMXKLwQvBY8M3gawXOrnR9VnbSiy9QIY2T6iU2CB1305ZcBghni+ovnlbyiaTtA+ftzLMIix74PoOU3cmVCiJppuGPX0PC0rucThs0ADFf6ZqWMITEsSSCIuJKsBQ=='
removequotes
delimiter ','
null as 'NULL'
/* noload */
;

copy pitch
from 's3://w210-pitch-prediction-test/gd_pitch.csv'
credentials 'aws_access_key_id=ASIAII4MFJ64ON27I6JQ;aws_secret_access_key=pKotUI7eodJIu1sjRitvMJwaO3qSM8opRo+WNOtm;token=AQoDYXdzEGgakAI6bAR5LX0fqLEhAgYqBR4V6O8HLP4Xar+P/swFy60y0P4lbriucIsrNdxNJP41TWc5U5VbEQ6gdkIP04jMk8/Ra0UkeneD1KqVw6ZWRP4jnPq/4MJjUHcWEA4mrDnDOV5AVOnpSLFFIGJhG91JDBNvgEU0EMHrt4puaB8ZCW2U1FoTTpl0m/arBtm61bFV/3UZUjIRwlYcKKVl8/YICd8b/LPmBhnb+uDNUhUORm15ljzqsSRr6BfYrtMXKLwQvBY8M3gawXOrnR9VnbSiy9QIY2T6iU2CB1305ZcBghni+ovnlbyiaTtA+ftzLMIix74PoOU3cmVCiJppuGPX0PC0rucThs0ADFf6ZqWMITEsSSCIuJKsBQ=='
removequotes
delimiter ','
null as 'NULL'
/* noload */
;