package workbench.patterns.l04;

import java.io.IOException;
import java.util.function.BiFunction;

/** A legacy SOAP client adapted to our port, plus a lambda adapter for a one-method port. */
public class SoapAdapterDemo {

    // the port our payment code depends on
    interface PaymentGateway { String charge(long amountMinor, String currency, String token); }

    // a vendor client we can't change: XML in, XML out, checked IOException on failure
    static final class LegacySoapClient {
        String submitTxn(String xml) throws IOException {
            if (xml.contains("tok_down")) throw new IOException("SOAP fault: 503 Service Unavailable");
            String token = xml.substring(xml.indexOf("tok='") + 5, xml.lastIndexOf("'"));
            return "<resp code='00' ref='R-" + token.toUpperCase() + "'/>";
        }
    }

    static final class GatewayUnavailable extends RuntimeException {
        GatewayUnavailable(String message, Throwable cause) { super(message, cause); }
    }

    // the adapter: implements our port, holds the vendor client, translates both ways
    record SoapGatewayAdapter(LegacySoapClient soap) implements PaymentGateway {
        public String charge(long amountMinor, String currency, String token) {
            String xml = "<txn amt='" + amountMinor + "' cur='" + currency + "' tok='" + token + "'/>";
            try {
                String resp = soap.submitTxn(xml);
                return resp.substring(resp.indexOf("ref='") + 5, resp.lastIndexOf("'"));   // vendor format ends here
            } catch (IOException e) {
                throw new GatewayUnavailable("issuer unreachable", e);                       // our exception, not theirs
            }
        }
    }

    // for a one-method port, a lambda is the adapter
    static PaymentGateway fromFunction(BiFunction<Long, String, String> legacyCharge) {
        return (amount, currency, token) -> legacyCharge.apply(amount, token);
    }

    public static void main(String[] args) {
        PaymentGateway gateway = new SoapGatewayAdapter(new LegacySoapClient());
        System.out.println("charged, ref " + gateway.charge(1_250, "EUR", "tok_42"));
        try {
            gateway.charge(1_250, "EUR", "tok_down");
        } catch (RuntimeException e) {
            System.out.println("caller sees " + e.getClass().getSimpleName() + ": " + e.getMessage());
        }
        PaymentGateway quick = fromFunction((amount, token) -> "QUICK-" + amount);
        System.out.println("lambda adapter: " + quick.charge(990, "EUR", "tok_7"));
    }
}
