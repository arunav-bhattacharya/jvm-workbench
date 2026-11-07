package workbench.performance.l05;

import jdk.jfr.Category;
import jdk.jfr.Description;
import jdk.jfr.Event;
import jdk.jfr.Label;
import jdk.jfr.Name;

/** One call to the card issuer, recorded by JFR next to the JVM's own events. */
@Name("workbench.IssuerCall")
@Label("Issuer Call")
@Category({"Workbench", "Payments"})
@Description("A call to the card issuer during authorization")
public class IssuerCallEvent extends Event {
    @Label("Merchant")
    String merchant;

    @Label("Amount (cents)")
    long amountCents;

    @Label("Approved")
    boolean approved;
}
