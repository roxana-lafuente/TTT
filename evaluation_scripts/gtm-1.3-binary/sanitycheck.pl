#!/usr/bin/perl
#
# sanitycheck.pl
# $Id: sanitycheck.pl,v 1.4 2003/05/26 13:23:55 turian Exp $
#
# Run a sanity check on the program output.
#

# You may need to change the way the program is invoked:
#$origcmd = "java gtm" and (-e "gtm.class" or die "Invoke make before running this script");
$origcmd = "java -jar gtm.jar" and (-e "gtm.jar" or die "gtm.jar not found");

################
# You won't need to change anything past this point

$optfil = "tests/optionlist";

$checktot = int(`wc -l $optfil`);
open(OPT, "< $optfil") || die $!;

$checkcnt = 1;
$passcnt = 0;
$difftxt = "";
while(<OPT>) {
	if (/(\S+)\s+(.*)/) {
		$checkname = $1;
		$opts = $2;

		print "Test $checkcnt of $checktot: ";

		$diff = `$origcmd $2 | diff - tests/${1}.out`;
		if ($diff eq "") {
			print "Passed\n";
			$passcnt++;
		} else {
			print "FAILED\n";
			$difftxt .= "${1} diff:\n$diff\n";
		}

		$checkcnt++;
	} else {
		die "Could not parse $optfil line: $_\n";
	}
}

print "\n$passcnt of $checktot tests passed.\n\n";

if ($passcnt != $checktot) {
	print "The following is the diff text of those tests that failed:\n";
	print $difftxt;
}
