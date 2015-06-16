from timer import TimerEntry
import NavigationInstance 

def recordService(service):
	if NavigationInstance.instance.getRecordings():
		for timer in NavigationInstance.instance.RecordTimer.timer_list:
			if timer.state == TimerEntry.StateRunning:
				if timer.justplay:
					pass
				else:
					timerservice = timer.service_ref.ref.toString()
					if timerservice == service:
						return 1
	return 0
