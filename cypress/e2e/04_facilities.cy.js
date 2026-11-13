describe('04 - Facilities Catalogue & Booking Workflow', () => {
  before(() => {
    cy.resetDb();
  });

  const getNextMonday = () => {
    const d = new Date();
    d.setDate(d.getDate() + ((1 + 7 - d.getDay()) % 7 || 7));
    const yyyy = d.getFullYear();
    const mm = String(d.getMonth() + 1).padStart(2, '0');
    const dd = String(d.getDate()).padStart(2, '0');
    return `${yyyy}-${mm}-${dd}`;
  };

  const getNextSunday = () => {
    const d = new Date();
    d.setDate(d.getDate() + ((7 - d.getDay()) % 7 || 7));
    const yyyy = d.getFullYear();
    const mm = String(d.getMonth() + 1).padStart(2, '0');
    const dd = String(d.getDate()).padStart(2, '0');
    return `${yyyy}-${mm}-${dd}`;
  };

  it('allows student to book GPU Compute Cluster on next Monday 10:00-11:00', () => {
    cy.loginAs('student');
    cy.visit('/facilities/');
    cy.contains('a', 'GPU Compute Cluster').first().click();
    cy.get('main').contains('a', /book/i).click();

    const nextMon = getNextMonday();
    cy.get('input[name="date"]').clear().type(nextMon);
    cy.get('input[name="start_time"]').clear().type('10:00');
    cy.get('input[name="end_time"]').clear().type('11:00');
    cy.get('input[name="purpose"]').clear().type('E2E Deep Learning Benchmark');
    cy.get('main button[type="submit"]').click();

    cy.url().should('include', '/facilities/my-bookings/');
    cy.contains('Booking requested').should('exist');
    cy.contains('GPU Compute Cluster').should('exist');
    cy.contains(/pending/i).should('exist');
  });

  it('rejects overlapping booking with slot conflict message', () => {
    cy.loginAs('student');
    cy.visit('/facilities/');
    cy.contains('a', 'GPU Compute Cluster').first().click();
    cy.get('main').contains('a', /book/i).click();

    const nextMon = getNextMonday();
    cy.get('input[name="date"]').clear().type(nextMon);
    cy.get('input[name="start_time"]').clear().type('10:30');
    cy.get('input[name="end_time"]').clear().type('11:30');
    cy.get('input[name="purpose"]').clear().type('Overlapping Booking Attempt');
    cy.get('main button[type="submit"]').click();

    cy.contains('That time was just taken. Please pick another slot.').should('exist');
  });

  it('allows back-to-back booking from 11:00-12:00', () => {
    cy.loginAs('student');
    cy.visit('/facilities/');
    cy.contains('a', 'GPU Compute Cluster').first().click();
    cy.get('main').contains('a', /book/i).click();

    const nextMon = getNextMonday();
    cy.get('input[name="date"]').clear().type(nextMon);
    cy.get('input[name="start_time"]').clear().type('11:00');
    cy.get('input[name="end_time"]').clear().type('12:00');
    cy.get('input[name="purpose"]').clear().type('Back-to-back Experiment');
    cy.get('main button[type="submit"]').click();

    cy.url().should('include', '/facilities/my-bookings/');
    cy.contains('Booking requested').should('exist');
  });

  it('shows closed hours error when attempting to book on Sunday', () => {
    cy.loginAs('student');
    cy.visit('/facilities/');
    cy.contains('a', 'GPU Compute Cluster').first().click();
    cy.get('main').contains('a', /book/i).click();

    const nextSun = getNextSunday();
    cy.get('input[name="date"]').clear().type(nextSun);
    cy.get('input[name="start_time"]').clear().type('10:00');
    cy.get('input[name="end_time"]').clear().type('11:00');
    cy.get('input[name="purpose"]').clear().type('Sunday Attempt');
    cy.get('main button[type="submit"]').click();

    cy.contains(/closed/i).should('exist');
  });

  it('custodian approves pending booking and student receives notification', () => {
    cy.loginAs('custodian');
    cy.visit('/facilities/manage/');
    cy.contains('GPU Compute Cluster').should('exist');
    cy.contains('tr', 'GPU Compute Cluster').find('button').contains(/approve/i).click();

    // Verify student receives approved notification
    cy.loginAs('student');
    cy.visit('/dashboard/notifications/');
    cy.contains(/approved/i).should('exist');
  });

  it('student cancels a future booking', () => {
    cy.loginAs('student');
    cy.visit('/facilities/my-bookings/');
    cy.get('button').contains(/cancel/i).first().click();
    cy.get('#confirmDialog').should('be.visible'); // destructive actions now confirm in an accessible dialog
    cy.get('#confirmAccept').click();
    cy.contains('Booking cancelled.').should('exist');
  });

  it('custodian views utilisation report and exports CSV', () => {
    cy.loginAs('custodian');
    cy.visit('/facilities/utilisation/');
    cy.get('table').should('contain', 'GPU Compute Cluster');

    cy.request('/facilities/utilisation/?format=csv').then((response) => {
      expect(response.status).to.eq(200);
      expect(response.body).to.include('Facility,Department,Open Hours,Used Hours,Idle Hours,Utilisation (%)');
    });
  });

  it('forbids student from viewing utilisation report (403)', () => {
    cy.loginAs('student');
    cy.request({
      url: '/facilities/utilisation/',
      failOnStatusCode: false,
    }).then((resp) => {
      expect(resp.status).to.eq(403);
    });
  });
});
