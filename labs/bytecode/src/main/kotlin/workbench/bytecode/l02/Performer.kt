package workbench.bytecode.l02

import java.io.IOException

/**
 * A performer on the theatre's books, written in Kotlin and called from the Java parts of the
 * show program. The Kotlin code works, but the JVM shape kotlinc produces is wrong for the Java
 * callers. The tests read that shape with reflection, the same members `javap -p` lists. Change
 * ONLY annotations, modifiers and the property name so that Java can:
 *
 * 1. read `Performer.MAX_SHOWS` as a static field;
 * 2. call `Performer.sign("ana")` as a static method;
 * 3. call `performer.book(2)` without passing the stage;
 * 4. read `getShows()` but find no public `setShows`;
 * 5. call `performer.isResting()` and `performer.setResting(true)`;
 * 6. catch the `IOException` that `exportCsv` can throw.
 *
 * Run `javap -p` on build/classes/kotlin/main/workbench/bytecode/l02/Performer.class before and after.
 */
class Performer(val name: String) {
    var shows: Int = 0

    var resting: Boolean = false

    fun book(count: Int, stage: String = "Main Stage"): Int {
        check(!resting) { "$name is resting this week" }
        require(stage == "Main Stage") { "only the Main Stage takes bookings, not $stage" }
        shows += count
        return shows
    }

    fun exportCsv(out: Appendable) {
        if (resting) throw IOException("export refused: $name is resting this week")
        out.append("$name,$shows\n")
    }

    companion object {
        val MAX_SHOWS = 8

        fun sign(name: String): Performer = Performer(name)
    }
}
