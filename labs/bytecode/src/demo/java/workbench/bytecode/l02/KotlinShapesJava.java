package workbench.bytecode.l02;

/** The Kotlin shapes from KotlinShapes.kt, called from Java: this is the API javap describes. */
public class KotlinShapesJava {
    public static void main(String[] args) {
        Payment p = new Payment("p-1", 1_250);             // Java must pass every argument
        Payment q = p.copy("p-2", 99);                       // copy() takes all of them too
        System.out.println(p.getAmountMinor() + " " + p.component1() + " " + q);

        Account a = Account.open("ana");                    // @JvmStatic: a real static method
        Account b = Account.Companion.create("bo");         // no @JvmStatic: through the Companion
        a.iban = "DE89 3704 0044 0532 0130 00";              // lateinit: a public field
        // a.setBalanceMinor(5);                             // does not compile: private set, no setter
        System.out.println(a.getBalanceMinor() + " " + a.isEmpty() + " " + b.getOwner());
        System.out.println("max=" + Account.MAX_MINOR + " currency=" + Account.Companion.getDEFAULT_CURRENCY());

        Registry.INSTANCE.getAccounts().add(a);              // object: a singleton behind INSTANCE
        System.out.println(KotlinShapesKt.greet("Bo", '?')); // top-level function: static on the file class
    }
}
