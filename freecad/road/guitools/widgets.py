# SPDX-License-Identifier: LGPL-2.1-or-later
import FreeCAD, FreeCADGui
from PySide.QtWidgets import QLineEdit
from PySide.QtCore import QTimer
from ..utils.trackers import ViewTracker

class GeoWidget(QLineEdit):
    def __init__(self):
        mw = FreeCADGui.getMainWindow()
        super().__init__(mw)
        mw.statusBar().addPermanentWidget(self)
        self.id = FreeCADGui.ActiveDocument.Document.Uid if FreeCADGui.ActiveDocument else None
        self.view = None
        self.tracker = None
        self.tracker_active = False
        
        # Timer for continuous checking
        self.check_timer = QTimer()
        self.check_timer.timeout.connect(self._check_and_start_tracker)
        self.check_timer.setInterval(1000)  # Check every second
        self.check_timer.start()
    
    def _check_and_start_tracker(self):
        """Check if view and GeoOrigin exist, then start tracker if both are present"""
        try:
            # Check if ActiveDocument and ActiveView exist
            doc = FreeCADGui.ActiveDocument
            if not doc:
                self._stop_tracker()
                return False
            
            # Check if document changed
            if self.id != doc.Document.Uid:
                self._stop_tracker()
                self.id = doc.Document.Uid
                return False
            
            # Check if view exists
            if not doc.ActiveView:
                self._stop_tracker()
                return False
            
            # Check if GeoOrigin exists
            origin = doc.Document.getObject("GeoOrigin")
            if not origin:
                self._stop_tracker()
                return False
            
            # Everything is ready, start tracker if not already active
            if not self.tracker_active:
                self._start_tracker()
            
            return True
            
        except Exception as e:
            print(f"Error in _check_and_start_tracker: {e}")
            self._stop_tracker()
            return False
    
    def _start_tracker(self):
        """Start the tracker"""
        if self.tracker_active:
            return
        
        try:
            doc = FreeCADGui.ActiveDocument
            if not doc or not doc.ActiveView:
                return
            
            super().show()
            self.tracker = ViewTracker(
                view=doc.ActiveView,  # Pass view explicitly
                eventid="Location", 
                function=self.coordinate_update, 
                cancelable=False, 
                selection=True
            )
            self.tracker.start()
            self.tracker_active = True
        except Exception as e:
            print(f"Error starting tracker: {e}")
            self.tracker_active = False
    
    def _stop_tracker(self):
        """Stop the tracker and hide widget"""
        if not self.tracker_active:
            return
        
        self.tracker_active = False
        
        try:
            if self.tracker:
                self.tracker.stop()
        except Exception as e:
            print(f"Error stopping tracker: {e}")
        finally:
            self.tracker = None
            super().hide()
    
    def show(self):
        """Override show - use _start_tracker instead"""
        pass
    
    def hide(self):
        """Override hide - use _stop_tracker instead"""
        pass
    
    def coordinate_update(self, callback):
        """Update coordinate display"""
        try:
            doc = FreeCADGui.ActiveDocument
            if not doc or not doc.ActiveView:
                return
            
            self.view = doc.ActiveView
            
            # Try to get coordinate from object
            try:
                obj = self.view.getObjectInfo(self.view.getCursorPos())
                coordinate = FreeCAD.Vector(obj["x"], obj["y"], obj["z"])
            except Exception:
                # Fallback: get coordinate from cursor position
                event = callback.getEvent()
                position = event.getPosition()  # Window position
                coordinate = self.view.getPoint(tuple(position.getValue()))
                coordinate.z = 0
            
            # Get origin and update display
            origin = FreeCAD.ActiveDocument.getObject("GeoOrigin")
            if origin:
                coordinate = coordinate.add(origin.Base)
                infoText = ", ".join([f"{value/1000:.3f}" for value in coordinate])
                self.setText(infoText)
                self.setMinimumWidth(200)
            else:
                self._stop_tracker()
                
        except Exception as e:
            print(f"Error in coordinate_update: {e}")
    
    def __del__(self):
        """Cleanup on deletion"""
        try:
            self.check_timer.stop()
            self._stop_tracker()
        except:
            pass