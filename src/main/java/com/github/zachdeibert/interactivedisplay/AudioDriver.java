package com.github.zachdeibert.interactivedisplay;

import org.eclipse.paho.client.mqttv3.IMqttDeliveryToken;
import org.eclipse.paho.client.mqttv3.MqttCallback;
import org.eclipse.paho.client.mqttv3.MqttClient;
import org.eclipse.paho.client.mqttv3.MqttConnectOptions;
import org.eclipse.paho.client.mqttv3.MqttException;
import org.eclipse.paho.client.mqttv3.MqttMessage;
import org.eclipse.paho.client.mqttv3.persist.MemoryPersistence;

import javax.sound.midi.*;

public class AudioDriver implements MqttCallback {
    private static MidiChannel channel;

    @Override
    public void connectionLost(Throwable cause) {
        System.err.println(cause);
    }

    @Override
    public void deliveryComplete(IMqttDeliveryToken token) {
    }

    @Override
    public void messageArrived(String topic, MqttMessage message) {
        if (topic.startsWith("interactive_display/audio/note/")) {
            String note = topic.substring("interactive_display/audio/note/".length());
            int noteId = Integer.parseInt(note);
            String msg = new String(message.getPayload());
            if (msg.equals("off")) {
                channel.noteOff(noteId);
            } else {
                int velocity = Integer.parseInt(msg);
                channel.noteOn(noteId, velocity);
            }
        }
    }

    public static void main(String[] args) throws Exception {
        Synthesizer synth = MidiSystem.getSynthesizer();
        synth.open();
        Instrument[] instruments = synth.getDefaultSoundbank().getInstruments();
        MidiChannel[] channels = synth.getChannels();
        synth.loadInstrument(instruments[0]);
        channel = channels[0];
        MemoryPersistence persistence = new MemoryPersistence();
        MqttClient client = new MqttClient("tcp://localhost:1883", "audio-driver", persistence);
        MqttConnectOptions opts = new MqttConnectOptions();
        opts.setCleanSession(true);
        client.connect(opts);
        client.setCallback(new AudioDriver());
        client.subscribe("interactive_display/audio/note/+");
        System.out.println("Ready.");
    }
}
