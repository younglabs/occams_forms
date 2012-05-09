#saconfig
from zope.interface import implements
from z3c.saconfig.utility import GloballyScopedSession
from zope import component
from z3c.saconfig.interfaces import IScopedSession, IEngineFactory
from sqlalchemy.orm import  sessionmaker, scoped_session
from AccessControl import getSecurityManager
from z3c.saconfig import named_scoped_session
from zope.component import getUtilitiesFor

from occams.datastore.model.session import DataStoreSession
from occams.datastore import model
from occams.form.interfaces import ISessionUserFactory
from sqlalchemy.exc import ProgrammingError
class EventAwareScopedSession(GloballyScopedSession):
    """A globally scoped session.

    Register this as a global utility to have just one kind of session
    per Zope instance. All applications in this instance will share the
    same session.

    To register as a global utility you may need to register it with
    a custom factory, or alternatively subclass it and override __init__
    to pass the right arguments to the superclasses __init__.
    """
    implements(IScopedSession)

    def sessionFactory(self):
        kw = self.kw.copy()
        if 'bind' not in kw:
            engine_factory = component.getUtility(IEngineFactory,
                                                  name=self.engine)
            kw['bind'] = engine_factory()
        if 'user' not in kw:
            user_factory = component.getUtility(ISessionUserFactory,
                                                  name='occams.SessionUserFactory')
            kw['user'] = user_factory
        if 'class_' not in kw:
            kw['class_'] = DataStoreSession
        return scoped_session(sessionmaker(**kw))

class SessionUserFactory(object):
    """
    Needs to be called "occams.SessionUserFactory"
    """
    implements(ISessionUserFactory)

    def __call__(self):
        """
        Get the id of the current user
        """
        return getSecurityManager().getUser().getId()

def registerUser(event):
    registered = getUtilitiesFor(IScopedSession)
    for name, utility in registered:
        if name.find('occams') >= 0:
            Session = named_scoped_session(name)
            try:
                userQ = Session.query(model.User).filter_by(key = event.principal.getId())
                if not userQ.count():
                    newUser= model.User(key = event.principal.getId())
                    Session.add(newUser)
                    Session.flush()
            except ProgrammingError:
                ## not a occams repository?!?!?
                continue