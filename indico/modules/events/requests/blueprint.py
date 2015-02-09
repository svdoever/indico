# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

from indico.modules.events.requests.controllers import (RHRequestsEventRequests, RHRequestsEventRequestDetails,
                                                        RHRequestsEventRequestWithdraw, RHRequestsEventRequestProcess)
from indico.web.flask.wrappers import IndicoBlueprint

requests_blueprint = _bp = IndicoBlueprint('requests', __name__, template_folder='templates')

# Event management
_bp.add_url_rule('/event/<confId>/manage/requests/', 'event_requests', RHRequestsEventRequests)
_bp.add_url_rule('/event/<confId>/manage/requests/<type>/', 'event_requests_details', RHRequestsEventRequestDetails,
                 methods=('GET', 'POST'))
_bp.add_url_rule('/event/<confId>/manage/requests/<type>/withdraw', 'event_requests_withdraw',
                 RHRequestsEventRequestWithdraw, methods=('POST',))
_bp.add_url_rule('/event/<confId>/manage/requests/<type>/process', 'event_requests_process',
                 RHRequestsEventRequestProcess, methods=('POST',))