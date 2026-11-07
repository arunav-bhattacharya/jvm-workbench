package workbench.concurrency.l08;

import java.util.concurrent.atomic.AtomicReference;
import java.util.concurrent.atomic.AtomicStampedReference;

/**
 * The ABA problem, played out by hand on one thread so it happens every time.
 * Nodes are recycled (mutable next), as in a pooled or off-heap structure.
 */
public class AbaDemo {
    static final class Node {
        final String name;
        Node next;
        Node(String name, Node next) { this.name = name; this.next = next; }
    }

    static String show(Node n) {
        StringBuilder sb = new StringBuilder();
        for (; n != null; n = n.next) sb.append(n.name).append(n.next != null ? " -> " : "");
        return sb.length() == 0 ? "(empty)" : sb.toString();
    }

    public static void main(String[] args) {
        Node c = new Node("C", null), b = new Node("B", c), a = new Node("A", b);

        AtomicReference<Node> head = new AtomicReference<>(a);
        System.out.println("start:                   " + show(head.get()));
        Node top = head.get(), next = top.next;                       // T1 starts a pop...
        System.out.println("T1 reads top=A, next=B, then is paused");
        head.set(b);                                                  // T2 pops A
        head.set(c);                                                  // T2 pops B (B is now T2's)
        a.next = head.get();
        head.set(a);                                                  // T2 pushes the recycled A
        System.out.println("T2 pops A, pops B, pushes A again: " + show(head.get()));
        boolean ok = head.compareAndSet(top, next);                   // T1 resumes: head is A again
        System.out.println("T1 resumes: compareAndSet(A, B) = " + ok);
        System.out.println("stack now:               " + show(head.get()) + "   (B was popped by T2: corrupted)");

        System.out.println();
        a.next = b; b.next = c;
        AtomicStampedReference<Node> stamped = new AtomicStampedReference<>(a, 0);
        int[] stampHolder = new int[1];
        Node top2 = stamped.get(stampHolder);                         // T1 reads the node AND the stamp
        int stamp = stampHolder[0];
        Node next2 = top2.next;
        System.out.println("T1 reads top=A, stamp=" + stamp + ", next=B, then is paused");
        stamped.set(b, 1);                                            // every change bumps the stamp
        stamped.set(c, 2);
        a.next = c;
        stamped.set(a, 3);
        System.out.println("T2 pops A, pops B, pushes A again: stamp is now " + stamped.getStamp());
        boolean ok2 = stamped.compareAndSet(top2, next2, stamp, stamp + 1);
        System.out.println("T1 resumes: compareAndSet(A, B, stamp " + stamp + ") = " + ok2 + ", so T1 re-reads and retries");
    }
}
