package main

import (
	"fmt"
	"strconv"
	"strings"

	MQTT "github.com/eclipse/paho.mqtt.golang"

	"./data"
)

var (
	c MQTT.Client
)

var handler MQTT.MessageHandler = func(client MQTT.Client, msg MQTT.Message) {
	if strings.HasPrefix(msg.Topic(), "interactive_display/touch_events/") {
		channel, err := strconv.Atoi(msg.Topic()[len("interactive_display/touch_events/"):])
		if err == nil {
			fmt.Println("Got event for channel %d\n", channel)
			for _, toneMap := range data.Tones {
				if toneMap.TouchChannel == channel {
					switch string(msg.Payload()) {
					case "on":
						c.Publish(fmt.Sprintf("interactive_display/audio/note/%d", toneMap.AudioNote), 0, false, strconv.FormatInt(int64(toneMap.Velocity), 10))
						break
					case "off":
						c.Publish(fmt.Sprintf("interactive_display/audio/note/%d", toneMap.AudioNote), 0, false, "off")
						break
					}
				}
			}
		}
	}
}

func main() {
	opts := MQTT.NewClientOptions().AddBroker("tcp://localhost:1883")
	opts.SetClientID("tones")
	opts.SetDefaultPublishHandler(handler)
	c = MQTT.NewClient(opts)
	if token := c.Connect(); token.Wait() && token.Error() != nil {
		panic(token.Error())
	}
	if token := c.Subscribe("interactive_display/touch_events/+", 0, nil); token.Wait() && token.Error() != nil {
		panic(token.Error())
	}
	select {}
}
