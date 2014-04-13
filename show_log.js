function loggedEventFactory(event_data) {
    return new LoggedEvent(event_data.event_name, event_data);
}

function LoggedEvent(type, data) {
    var self = this;

    self.type = type;
    self.additional_data = data;
}

function EventsStreamViewModel() {
    var self = this;

    self.events = ko.observableArray();
    self.playbook = ko.computed({
        read: function () {
            var parser = new EventsParser();
            $.each(self.events(), function () {
                parser.push_event(this.additional_data);
            });
            return parser.get_playbook();
        },
        deferEvaluation: true
    });

    self.loadEventsFromServer();
}

EventsStreamViewModel.prototype.loadEventsFromServer = function () {
    var self = this;

    $.each(event_stream.stream, function () { self.addRawEvent(this); });

/*
    $.ajax(
	'play_log.json',
	function (data) {
	    console.log(data);
	    var stream_obj = $.parseJSON(data);
	    $.each(stream_obj.stream, function (raw_event) {
		self.addRawEvent(raw_event);
	    });
	});
*/
}

EventsStreamViewModel.prototype.addRawEvent = function (raw_event) {
    var self = this;

    if (raw_event.event_name) {
	self.events.push(loggedEventFactory(raw_event));
    }
}

ko.bindingHandlers.foreachprop = {
    transformObject: function (obj) {
        var properties = [];
        for (var key in obj) {
            if (obj.hasOwnProperty(key)) {
                properties.push({ key: key, value: obj[key] });
            }
        }
        return properties;
    },
    init: function(element, valueAccessor, allBindingsAccessor, viewModel, bindingContext) {
        var value = ko.utils.unwrapObservable(valueAccessor()),
            properties = ko.bindingHandlers.foreachprop.transformObject(value);
        ko.applyBindingsToNode(element, { foreach: properties });
        return { controlsDescendantBindings: true };
    }
};

ko.applyBindings(new EventsStreamViewModel());
