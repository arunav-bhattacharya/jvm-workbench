package workbench.coroutines.l03

import kotlinx.coroutines.CoroutineName
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Job
import kotlinx.coroutines.async
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.delay
import kotlinx.coroutines.job
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking

/** Prints a Job and all of its children, indented. */
fun Job.printTree(indent: String = "") {
    // every coroutine is also a CoroutineScope, so we can read the name from its context
    val name = (this as? CoroutineScope)?.coroutineContext?.get(CoroutineName)?.name ?: "(coroutineScope)"
    println("$indent$name  active=$isActive  children=${children.count()}")
    children.forEach { it.printTree("$indent    ") }
}

fun main() = runBlocking(CoroutineName("dinner")) {
    val course = launch(CoroutineName("main-course")) {
        coroutineScope {
            async(CoroutineName("roast")) { delay(300) }
            async(CoroutineName("potatoes")) { delay(300) }
            launch(CoroutineName("gravy")) { delay(300) }
            delay(100) // give the children time to start
            println("tree at 100 ms, seen from the dinner coroutine:")
            this@runBlocking.coroutineContext.job.printTree()
        }
    }
    course.join()
    println("after join: dinner has ${coroutineContext.job.children.count()} children")
}
