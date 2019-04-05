package main

import (
	"fmt"
	"strings"

	MQTT "github.com/eclipse/paho.mqtt.golang"
)

var handler MQTT.MessageHandler = func(client MQTT.Client, msg MQTT.Message) {
	if strings.HasPrefix(msg.Topic(), "interactive_display/touch_events/") {
		fmt.Printf("channel %s: %s\n", msg.Topic()[len("interactive_display/touch_events/"):], msg.Payload())
	}
}

func main() {
	opts := MQTT.NewClientOptions().AddBroker("tcp://localhost:1883")
	opts.SetClientID("calibration")
	opts.SetDefaultPublishHandler(handler)
	c := MQTT.NewClient(opts)
	if token := c.Connect(); token.Wait() && token.Error() != nil {
		panic(token.Error())
	}
	if token := c.Subscribe("interactive_display/touch_events/+", 0, nil); token.Wait() && token.Error() != nil {
		panic(token.Error())
	}
	select {}
}
