package workbench.performance.l05;

import jdk.jfr.Category;
import jdk.jfr.Description;
import jdk.jfr.Event;
import jdk.jfr.Label;
import jdk.jfr.Name;

@Name("workbench.Authorization")                   // the stable name tools and queries use
@Label("Card Authorization")                        // what JMC and `jfr view` show
@Category({"Workbench", "Payments"})
@Description("One authorization, timed from the issuer call to its answer")
public class AuthorizationEvent extends Event {
    @Label("Merchant")
    String merchant;

    @Label("Amount (cents)")
    long amountCents;

    @Label("Approved")
    boolean approved;
}
