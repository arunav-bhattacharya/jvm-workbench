package workbench.kotlin.l05.demo

interface Logbook {
    fun write(line: String)
}

class Shift(val name: String)

data class Job(val file: String, val copies: Int)

/** Two context parameters, then an extension receiver, then an ordinary parameter. */
context(logbook: Logbook, shift: Shift)
fun Job.check(printer: String): Boolean {
    logbook.write("[${shift.name}] checking $copies copies of $file for $printer")
    return copies <= 1_000
}

/** Calls check and remark without passing the logbook or the shift: the context flows on. */
context(logbook: Logbook, shift: Shift)
fun takeIn(job: Job, printer: String): String {
    val ok = job.check(printer)
    remark("${job.file} ${if (ok) "accepted" else "refused"} on the ${shift.name} shift")
    return if (ok) "ACCEPTED" else "REFUSED"
}

/** An anonymous context parameter, read with contextOf. */
context(_: Logbook)
fun remark(event: String) = contextOf<Logbook>().write("NOTE $event")

fun main() {
    val console = object : Logbook {
        override fun write(line: String) = println(line)
    }
    context(console, Shift("early")) {
        println(takeIn(Job("flyer.pdf", 250), "laser-1"))
        println(takeIn(Job("posters.pdf", 5_000), "laser-2"))
    }
    with(console) { remark("an implicit receiver works too") }

    // Wrong move. Uncomment, predict, run.
    // takeIn(Job("menu.pdf", 40), "laser-1")
}
