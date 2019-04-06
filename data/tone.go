package data

type toneMapping struct {
	TouchChannel int
	AudioNote    int
	Velocity     int
}

func toneMap(touchChannel int, audioNote int, velocity int) toneMapping {
	return toneMapping{
		TouchChannel: touchChannel,
		AudioNote:    audioNote,
		Velocity:     velocity,
	}
}
