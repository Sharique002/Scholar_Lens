import 'cypress-axe';
import './commands';

before(() => {
  cy.resetDb();
});
