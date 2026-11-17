package workbench.kotlin.l06.demo

import workbench.kotlin.NoArgEntity

/** no-arg adds a zero-argument constructor that only Java and reflection can call. */
@NoArgEntity
class JobRow(val id: String, var pages: Int) {
    var status: String = "NEW"
}

fun main() {
    // the way a database library builds an empty object before it fills in the columns
    val blank = JobRow::class.java.getDeclaredConstructor().newInstance()
    println("blank.pages = ${blank.pages}")
    println("blank.status is null: ${(blank.status as String?) == null}")   // declared String, holds null
    println("normal status = ${JobRow("job-1", 12).status}")

    // Wrong move. Uncomment, predict, run.
    // val direct = JobRow()
}
