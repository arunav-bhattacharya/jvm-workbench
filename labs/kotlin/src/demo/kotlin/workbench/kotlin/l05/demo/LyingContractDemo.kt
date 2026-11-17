package workbench.kotlin.l05.demo

import kotlin.contracts.ExperimentalContracts
import kotlin.contracts.contract

/** A contract that lies. The compiler checks neither the promise nor the body. */
@OptIn(ExperimentalContracts::class)
fun JobEvent.lyingIsPrinted(): Boolean {
    contract { returns(true) implies (this@lyingIsPrinted is Printed) }
    return true
}

fun main() {
    val jammed: JobEvent = Jammed("job-8", "laser-1")
    try {
        if (jammed.lyingIsPrinted()) println("printed ${jammed.pages} pages")
    } catch (e: ClassCastException) {
        println("ClassCastException: ${e.message}")
    }
}
