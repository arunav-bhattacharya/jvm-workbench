package workbench.kotlin.l06.demo;

/**
 * Java twin of NoArgDemo.kt. Java can call the generated constructor directly: it is hidden from
 * Kotlin with @Deprecated(level = HIDDEN), which javac doesn't enforce.
 */
public class NoArgDemoJava {
    public static void main(String[] args) {
        LedgerRow blank = new LedgerRow();                 // compiles in Java
        System.out.println("blank.amountMinor = " + blank.getAmountMinor());
        System.out.println("blank.note = " + blank.getNote());   // null: the initializer never ran
        System.out.println("blank.getId() = " + blank.getId());
    }
}
