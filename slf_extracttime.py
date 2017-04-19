#!/usr/bin/python3
"""
@brief:
exporter les enregistrements voulus

@info:
* sélection par position (0 = premier, -1 = dernier)
* sélection par temps (plus proche valeur)
"""

import sys

from common.arg_command_line import myargparse
from slf import Serafin, common_data


def getSelaFrame(inname, outname, overwrite, posList, timeList):
    """
    Export frames from a Serafin file with a 0-based indexing list.
    A negative position accesses elements from the end of the list counting backwards (-1 returns the last
    frame)
    """
    # Check unicity of method
    if posList and timeList:
        sys.exit("Precise either posList or timeList")
    if not posList and not timeList:
        sys.exit("Precise a posList or a timeList")
        # posList = range(len(resin.time))

    with Serafin.Read(inname) as resin:
        resin.readHeader()
        resin.get_time()

        if timeList:
            posList = []
            for time in timeList:
                posList.append(min(range(len(resin.time)), key=lambda i: abs(resin.time[i]-time)))
            print("Position(s) found = {}".format(posList))

        with Serafin.Write(outname, overwrite) as resout:
            resout.copy_header(resin)
            resout.write_header()

            for pos in posList:
                try:
                    time = resin.time[pos]
                except IndexError:
                    sys.exit("ERROR: position n°{} is not in range [{},{}] (or in opposite interval)".format(pos,1,len(resin.time)))
                common_data.log("Write frame number {} (time = {})".format(pos, time))
                var = resin.read_entire_frame(time)
                resout.write_entire_frame(time, var)

if __name__ == '__main__':
    parser = myargparse(description=__doc__, add_args=['force', 'verbose'])
    parser.add_argument("inname", help="Serafin input filename")
    parser.add_argument("outname", help="Serafin output filename")
    parser.add_argument("--pos", nargs='+', type=int, help="frame position(s) (starting at 0)")
    parser.add_argument("--time", nargs='+', type=int, help="time (in seconds)")
    args = parser.parse_args()

    common_data.verbose = args.verbose

    try:
        getSelaFrame(args.inname, args.outname, args.force, args.pos, args.time)
    except FileExistsError as error:
        sys.exit("ERROR: {}".format(error))
