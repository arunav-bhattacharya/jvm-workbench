package workbench.bytecode.l02

import java.io.IOException

class Performer(val name: String) {
    var shows: Int = 0
        private set                        // 4. getter only: kotlinc emits no setter method

    var isResting: Boolean = false         // 5. a property named isX gets isX() and setX()

    @JvmOverloads                          // 3. also emit book(int) that fills in the default
    fun book(count: Int, stage: String = "Main Stage"): Int {
        check(!isResting) { "$name is resting this week" }
        require(stage == "Main Stage") { "only the Main Stage takes bookings, not $stage" }
        shows += count
        return shows
    }

    @Throws(IOException::class)            // 6. write `throws IOException` into the method, for javac
    fun exportCsv(out: Appendable) {
        if (isResting) throw IOException("export refused: $name is resting this week")
        out.append("$name,$shows\n")
    }

    companion object {
        const val MAX_SHOWS = 8                     // 1. public static final int on Performer

        @JvmStatic                                  // 2. a static Performer.sign, not only Companion.sign
        fun sign(name: String): Performer = Performer(name)
    }
}
