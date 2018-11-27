#!/usr/bin/env python

#  Tool to collect project data and publish to IATI
#
#  Copyright (C) 2015 Mark Brough
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

from flask_script import Manager
import maediprojects

def run():
    manager = Manager(maediprojects.app)
    manager.run()

if __name__ == "__main__":
    run()
