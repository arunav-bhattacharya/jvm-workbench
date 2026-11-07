package workbench.concurrency.l08

import java.util.concurrent.atomic.AtomicReference
import java.util.concurrent.atomic.AtomicStampedReference

// The ABA problem, played out by hand on one thread so it happens every time.
// Nodes are recycled (mutable next), as in a pooled or off-heap structure.
private class AbaNode(val name: String, var next: AbaNode?)

private fun show(start: AbaNode?): String =
    generateSequence(start) { it.next }.joinToString(" -> ") { it.name }.ifEmpty { "(empty)" }

fun main() {
    val c = AbaNode("C", null)
    val b = AbaNode("B", c)
    val a = AbaNode("A", b)

    val head = AtomicReference(a)
    println("start:                   ${show(head.get())}")
    val top = head.get()
    val next = top.next                                           // T1 starts a pop...
    println("T1 reads top=A, next=B, then is paused")
    head.set(b)                                                   // T2 pops A
    head.set(c)                                                   // T2 pops B (B is now T2's)
    a.next = head.get()
    head.set(a)                                                   // T2 pushes the recycled A
    println("T2 pops A, pops B, pushes A again: ${show(head.get())}")
    val ok = head.compareAndSet(top, next)                        // T1 resumes: head is A again
    println("T1 resumes: compareAndSet(A, B) = $ok")
    println("stack now:               ${show(head.get())}   (B was popped by T2: corrupted)")

    println()
    a.next = b; b.next = c
    val stamped = AtomicStampedReference(a, 0)
    val stampHolder = IntArray(1)
    val top2 = stamped.get(stampHolder)                           // T1 reads the node AND the stamp
    val stamp = stampHolder[0]
    val next2 = top2.next
    println("T1 reads top=A, stamp=$stamp, next=B, then is paused")
    stamped.set(b, 1)                                             // every change bumps the stamp
    stamped.set(c, 2)
    a.next = c
    stamped.set(a, 3)
    println("T2 pops A, pops B, pushes A again: stamp is now ${stamped.stamp}")
    val ok2 = stamped.compareAndSet(top2, next2, stamp, stamp + 1)
    println("T1 resumes: compareAndSet(A, B, stamp $stamp) = $ok2, so T1 re-reads and retries")
}
