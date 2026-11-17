package workbench.kotlin.l05.demo;

import kotlin.Unit;

/**
 * Java twin of ContractsDemo.kt. Java has no contracts. It has no null checks in the type system to
 * satisfy, its instanceof pattern binds a new variable instead of smart-casting, and a lambda may
 * not assign a local variable at all.
 */
public class ContractsDemoJava {
    public static void main(String[] args) {
        String paper = ContractsDemoKt.lookupPaper("laser-1");
        ContractsDemoKt.requirePaper(paper);                    // to Java: a void method, nothing more
        System.out.println("paper = " + paper.toUpperCase());

        JobEvent event = new Printed("job-7", 12);
        if (event instanceof Printed p) {                       // the pattern binds p: no promise needed
            System.out.println("printed " + p.getPages() + " pages");
        }

        // String label; once(() -> { label = "x"; ... }) would not compile:
        // "local variables referenced from a lambda expression must be final or effectively final"
        String[] label = new String[1];
        ContractsDemoKt.once(() -> { label[0] = "job-17"; return Unit.INSTANCE; });
        System.out.println("label = " + label[0]);
    }
}
