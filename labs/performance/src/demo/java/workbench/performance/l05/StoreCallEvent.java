package workbench.performance.l05;

import jdk.jfr.Category;
import jdk.jfr.Description;
import jdk.jfr.Event;
import jdk.jfr.Label;
import jdk.jfr.Name;

/** One call to the document store, recorded by JFR next to the JVM's own events. */
@Name("workbench.StoreCall")
@Label("Store Call")
@Category({"Workbench", "Reports"})
@Description("A call to the document store while writing a report")
public class StoreCallEvent extends Event {
    @Label("Shelf")
    String shelf;

    @Label("Words")
    long words;

    @Label("Found")
    boolean found;
}
