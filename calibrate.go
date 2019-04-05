package main

import (
	"fmt"

	MQTT "github.com/eclipse/paho.mqtt.golang"
)

var handler MQTT.MessageHandler = func(client MQTT.Client, msg MQTT.Message) {
	fmt.Printf("Topic: %s, message: %s\n", msg.Topic(), msg.Payload())
}

func main() {
	opts := MQTT.NewClientOptions().AddBroker("tcp://localhost:1883")
	opts.SetClientID("calibration")
	opts.SetDefaultPublishHandler(handler)
	c := MQTT.NewClient(opts)
	if token := c.Connect(); token.Wait() && token.Error() != nil {
		panic(token.Error())
	}
	if token := c.Subscribe("#", 0, nil); token.Wait() && token.Error() != nil {
		panic(token.Error())
	}
}
