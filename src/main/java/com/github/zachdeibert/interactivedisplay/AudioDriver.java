package com.github.zachdeibert.interactivedisplay;

import org.eclipse.paho.client.mqttv3.IMqttDeliveryToken;
import org.eclipse.paho.client.mqttv3.MqttCallback;
import org.eclipse.paho.client.mqttv3.MqttClient;
import org.eclipse.paho.client.mqttv3.MqttConnectOptions;
import org.eclipse.paho.client.mqttv3.MqttException;
import org.eclipse.paho.client.mqttv3.MqttMessage;
import org.eclipse.paho.client.mqttv3.persist.MemoryPersistence;

public class AudioDriver implements MqttCallback {
    @Override
    public void connectionLost(Throwable cause) {
        System.err.println(cause);
    }

    @Override
    public void deliveryComplete(IMqttDeliveryToken token) {
    }

    @Override
    public void messageArrived(String topic, MqttMessage message) {
        if (topic.equals("interactive_display/audio/note")) {
            String msg = new String(message.getPayload());
            System.out.printf("Playing note %s...\n", msg); // TODO
        }
    }

    public static void main(String[] args) throws Exception {
        MemoryPersistence persistence = new MemoryPersistence();
        MqttClient client = new MqttClient("tcp://localhost:1883", "audio-driver", persistence);
        MqttConnectOptions opts = new MqttConnectOptions();
        opts.setCleanSession(true);
        client.connect(opts);
        client.setCallback(new AudioDriver());
        client.subscribe("interactive_display/audio/note");
    }
}
