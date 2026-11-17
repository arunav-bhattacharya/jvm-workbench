package workbench.bytecode.l07

/** The theatre's sound board. A final Kotlin class (no `open`): a subclass proxy couldn't touch it, an agent can. */
class SoundBoard {
    fun play(cue: String): String {
        played++
        return "played $cue"
    }

    /** Calls play on `this`: a forwarding proxy would miss these calls. */
    fun playAll(cues: List<String>): Int {
        cues.forEach { play(it) }
        return cues.size
    }

    fun check(cue: String) = "checked $cue"

    companion object {
        @JvmField var played = 0
    }
}
