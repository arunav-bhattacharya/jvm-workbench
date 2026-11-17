package workbench.patterns.l04;

import java.io.IOException;
import java.util.function.BiFunction;

/** An old courier client adapted to our port, plus a lambda adapter for a one-method port. */
public class XmlAdapterDemo {

    // the port our shop code depends on
    interface Courier { String book(String address, int grams); }

    // a client we can't change: XML text in, XML text out, checked IOException on failure
    static final class OldCourierClient {
        String submit(String xml) throws IOException {
            if (xml.contains("Nowhere")) throw new IOException("courier office closed: 503");
            String grams = xml.substring(xml.indexOf("grams='") + 7, xml.indexOf("' to="));
            return "<ok ref='R-" + grams + "'/>";
        }
    }

    static final class CourierUnavailable extends RuntimeException {
        CourierUnavailable(String message, Throwable cause) { super(message, cause); }
    }

    // the adapter: implements our port, holds the old client, translates both ways
    record OldCourierAdapter(OldCourierClient old) implements Courier {
        public String book(String address, int grams) {
            String xml = "<parcel grams='" + grams + "' to='" + address + "'/>";
            try {
                String answer = old.submit(xml);
                return answer.substring(answer.indexOf("ref='") + 5, answer.lastIndexOf("'"));   // their format ends here
            } catch (IOException e) {
                throw new CourierUnavailable("courier unreachable", e);                          // our exception, not theirs
            }
        }
    }

    // for a one-method port, a lambda is the adapter
    static Courier fromFunction(BiFunction<String, Integer, String> oldBook) {
        return (address, grams) -> oldBook.apply(address, grams);
    }

    public static void main(String[] args) {
        Courier courier = new OldCourierAdapter(new OldCourierClient());
        System.out.println("booked, ref " + courier.book("12 Mill Lane", 2_500));
        try {
            courier.book("1 Nowhere Road", 2_500);
        } catch (RuntimeException e) {
            System.out.println("caller sees " + e.getClass().getSimpleName() + ": " + e.getMessage());
        }
        Courier quick = fromFunction((address, grams) -> "QUICK-" + grams);
        System.out.println("lambda adapter: " + quick.book("3 Pier Street", 990));
    }
}
